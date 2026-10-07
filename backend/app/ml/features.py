"""Network Feature Engineering Module

Computes dynamic rolling statistics, rate-of-change indicators, and traffic trends
while strictly guarding against temporal data leakage.
"""

from typing import List, Dict, Any, Optional, Deque
from collections import deque
import numpy as np
import pandas as pd


# Core feature names expected by the ML model
BASE_NUMERIC_FEATURES = [
    "latency",
    "packet_loss",
    "jitter",
    "download_bandwidth",
    "upload_bandwidth",
    "traffic_rate",
    "network_utilization"
]

ENGINEERED_FEATURES = [
    "latency_rolling_mean",
    "latency_rolling_std",
    "packet_loss_rolling_mean",
    "jitter_rolling_mean",
    "latency_change_rate",
    "packet_loss_change_rate",
    "bandwidth_trend",
    "traffic_utilization_ratio",
    "signal_strength_imputed",
    "signal_strength_missing"
]

CATEGORICAL_FEATURES = ["connection_type"]

ALL_MODEL_FEATURES = BASE_NUMERIC_FEATURES + ENGINEERED_FEATURES + CATEGORICAL_FEATURES


class FeatureEngineer:
    """Computes features for offline datasets and real-time streaming telemetry."""

    @staticmethod
    def engineer_batch_dataframe(df: pd.DataFrame, window_size: int = 5) -> pd.DataFrame:
        """Transforms a batch DataFrame by adding chronological rolling and trend features.
        
        STRICT LEAKAGE PREVENTION:
        Only past and present rows (closed='left' or right with shift) within a rolling window
        are used. No forward-looking calculations.
        """
        data = df.copy()

        # Ensure sorted by timestamp if available
        if "timestamp" in data.columns:
            data = data.sort_values(by="timestamp").reset_index(drop=True)

        # 1. Rolling statistics (min_periods=1 ensures no NaNs at beginning)
        data["latency_rolling_mean"] = data["latency"].rolling(window=window_size, min_periods=1).mean()
        data["latency_rolling_std"] = data["latency"].rolling(window=window_size, min_periods=1).std().fillna(0.0)

        data["packet_loss_rolling_mean"] = data["packet_loss"].rolling(window=window_size, min_periods=1).mean()
        data["jitter_rolling_mean"] = data["jitter"].rolling(window=window_size, min_periods=1).mean()

        bw_rolling_mean = data["download_bandwidth"].rolling(window=window_size, min_periods=1).mean()
        data["bandwidth_trend"] = data["download_bandwidth"] - bw_rolling_mean

        # 2. Rates of change between consecutive intervals (dt = 1 step)
        prev_latency = data["latency"].shift(1).fillna(data["latency"])
        data["latency_change_rate"] = (data["latency"] - prev_latency) / np.maximum(prev_latency, 1.0)

        prev_loss = data["packet_loss"].shift(1).fillna(data["packet_loss"])
        data["packet_loss_change_rate"] = data["packet_loss"] - prev_loss

        # 3. Normalized utilization ratio (0.0 to 1.0)
        data["traffic_utilization_ratio"] = (data["network_utilization"] / 100.0).clip(0.0, 1.0)

        # 4. Signal strength missingness & imputation
        data["signal_strength_missing"] = data["signal_strength"].isnull().astype(float)
        # For Ethernet/missing, imputed with neutral median 0.0, explicitly preserved by missing indicator
        data["signal_strength_imputed"] = data["signal_strength"].fillna(0.0)

        return data


class StreamingFeatureEngineer:
    """Stateful rolling feature engineer for real-time live inference."""

    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.latency_buffer: Deque[float] = deque(maxlen=window_size)
        self.loss_buffer: Deque[float] = deque(maxlen=window_size)
        self.jitter_buffer: Deque[float] = deque(maxlen=window_size)
        self.bw_buffer: Deque[float] = deque(maxlen=window_size)
        self.prev_latency: Optional[float] = None
        self.prev_loss: Optional[float] = None

    def transform_single(self, telemetry_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Transforms a single incoming telemetry dictionary into the complete feature vector."""
        lat = float(telemetry_dict.get("latency", 0.0))
        loss = float(telemetry_dict.get("packet_loss", 0.0))
        jit = float(telemetry_dict.get("jitter", 0.0))
        bw = float(telemetry_dict.get("download_bandwidth", 0.0))
        up_bw = float(telemetry_dict.get("upload_bandwidth", 0.0))
        rate = float(telemetry_dict.get("traffic_rate", 0.0))
        util = float(telemetry_dict.get("network_utilization", 0.0))
        conn_type = str(telemetry_dict.get("connection_type", "Unknown"))
        signal = telemetry_dict.get("signal_strength")

        # Update buffers
        self.latency_buffer.append(lat)
        self.loss_buffer.append(loss)
        self.jitter_buffer.append(jit)
        self.bw_buffer.append(bw)

        # Compute rolling stats
        lat_rolling_mean = float(np.mean(self.latency_buffer))
        lat_rolling_std = float(np.std(self.latency_buffer)) if len(self.latency_buffer) > 1 else 0.0
        loss_rolling_mean = float(np.mean(self.loss_buffer))
        jit_rolling_mean = float(np.mean(self.jitter_buffer))
        bw_rolling_mean = float(np.mean(self.bw_buffer))

        # Rates of change
        if self.prev_latency is not None:
            lat_change = (lat - self.prev_latency) / max(self.prev_latency, 1.0)
        else:
            lat_change = 0.0

        if self.prev_loss is not None:
            loss_change = loss - self.prev_loss
        else:
            loss_change = 0.0

        self.prev_latency = lat
        self.prev_loss = loss

        bw_trend = bw - bw_rolling_mean
        util_ratio = min(1.0, max(0.0, util / 100.0))

        is_missing_sig = 1.0 if (signal is None or np.isnan(signal)) else 0.0
        imputed_sig = 0.0 if is_missing_sig == 1.0 else float(signal)

        features = {
            "latency": lat,
            "packet_loss": loss,
            "jitter": jit,
            "download_bandwidth": bw,
            "upload_bandwidth": up_bw,
            "traffic_rate": rate,
            "network_utilization": util,
            "connection_type": conn_type,
            "latency_rolling_mean": round(lat_rolling_mean, 2),
            "latency_rolling_std": round(lat_rolling_std, 2),
            "packet_loss_rolling_mean": round(loss_rolling_mean, 2),
            "jitter_rolling_mean": round(jit_rolling_mean, 2),
            "latency_change_rate": round(lat_change, 3),
            "packet_loss_change_rate": round(loss_change, 3),
            "bandwidth_trend": round(bw_trend, 2),
            "traffic_utilization_ratio": round(util_ratio, 3),
            "signal_strength_imputed": round(imputed_sig, 1),
            "signal_strength_missing": is_missing_sig
        }
        return features
