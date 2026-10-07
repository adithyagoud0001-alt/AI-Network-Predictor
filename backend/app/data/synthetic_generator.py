"""Network Telemetry Dataset Generator

Generates realistic network telemetry sequences representing real-world networking phenomena
(normal operation, link congestion, signal fading, bufferbloat, packet loss bursts, interface disconnects).

DOCUMENTATION ON HEURISTIC TARGET LABELS:
The multiclass target variable `heuristic_quality_label` (GOOD, MODERATE, POOR) in this dataset
is derived using explicit QoS operational threshold rules based on ITU-T G.1010 / ITU-T Y.1541
recommendations.
It represents a deterministic operational HEURISTIC TARGET, NOT AN ABSOLUTE GROUND TRUTH.
All threshold boundaries are parameterizable and fully inspectable.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path


class HeuristicLabelingConfig:
    """Configurable threshold rules defining operational connection quality classes."""

    # Latency thresholds (ms)
    LATENCY_GOOD_MAX: float = 60.0
    LATENCY_MODERATE_MAX: float = 140.0

    # Packet loss thresholds (%)
    LOSS_GOOD_MAX: float = 0.5
    LOSS_MODERATE_MAX: float = 4.0

    # Jitter thresholds (ms)
    JITTER_GOOD_MAX: float = 8.0
    JITTER_MODERATE_MAX: float = 25.0

    # Bandwidth minimums (Mbps)
    BANDWIDTH_GOOD_MIN: float = 20.0
    BANDWIDTH_MODERATE_MIN: float = 5.0

    # Wi-Fi signal strength minimums (%)
    WIFI_SIGNAL_GOOD_MIN: float = 65.0
    WIFI_SIGNAL_MODERATE_MIN: float = 40.0

    @classmethod
    def assign_heuristic_label(
        cls,
        latency: float,
        packet_loss: float,
        jitter: float,
        download_bw: float,
        network_utilization: float,
        signal_strength: Optional[float]
    ) -> str:
        """Assigns heuristic class: GOOD, MODERATE, or POOR.

        Decision Rationale:
        1. POOR: Unacceptable degradation on any critical transport metric
           - Packet loss > 4% (causes severe TCP retransmission collapses)
           - OR Latency > 140ms (poor interactive QoS)
           - OR Jitter > 25ms (degrades real-time voice/video)
           - OR Download Bandwidth < 5 Mbps with high utilization > 90%
           - OR Wi-Fi signal < 40% with loss > 2%
        2. GOOD: All metrics are within ideal QoS limits
           - Latency <= 60ms AND Packet Loss <= 0.5% AND Jitter <= 8ms
           - AND (signal_strength is None OR signal_strength >= 65%)
        3. MODERATE: Intermediate performance or mild degradation.
        """
        if (
            packet_loss > cls.LOSS_MODERATE_MAX or
            latency > cls.LATENCY_MODERATE_MAX or
            jitter > cls.JITTER_MODERATE_MAX or
            (download_bw < cls.BANDWIDTH_MODERATE_MIN and network_utilization > 85.0) or
            (signal_strength is not None and signal_strength < cls.WIFI_SIGNAL_MODERATE_MIN and packet_loss > 2.0)
        ):
            return "POOR"

        if (
            latency <= cls.LATENCY_GOOD_MAX and
            packet_loss <= cls.LOSS_GOOD_MAX and
            jitter <= cls.JITTER_GOOD_MAX and
            download_bw >= cls.BANDWIDTH_GOOD_MIN and
            (signal_strength is None or signal_strength >= cls.WIFI_SIGNAL_GOOD_MIN)
        ):
            return "GOOD"

        return "MODERATE"


def generate_synthetic_telemetry_dataset(
    num_samples: int = 5000,
    random_seed: int = 42,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """Generates synthetic network telemetry data covering diverse network environments.

    Environments simulated:
    - Fiber / High-Speed Ethernet (Low latency, 0% loss, null RSSI)
    - Pristine Wi-Fi (Good signal, low jitter)
    - Distant / Attenuated Wi-Fi (Low signal, fluctuating latency & jitter)
    - Congested / Bufferbloat link (High throughput, latency spikes, queue delay)
    - Intermittent / Lossy Link (Packet drop bursts, moderate latency)
    - Severe degradation / Outage transition (High loss, extreme latency)
    """
    np.random.seed(random_seed)

    records: List[Dict[str, Any]] = []
    base_time = datetime.now(timezone.utc) - timedelta(seconds=num_samples * 5)

    # Scenarios distribution
    scenarios = [
        ("pristine_ethernet", 0.25),
        ("good_wifi", 0.25),
        ("edge_wifi", 0.15),
        ("congested_link", 0.15),
        ("lossy_link", 0.12),
        ("severely_degraded", 0.08)
    ]
    scenario_names = [s[0] for s in scenarios]
    scenario_weights = [s[1] for s in scenarios]

    chosen_scenarios = np.random.choice(scenario_names, size=num_samples, p=scenario_weights)

    cum_bytes_sent = 10_000_000
    cum_bytes_recv = 50_000_000
    cum_pkts_sent = 20_000
    cum_pkts_recv = 70_000

    for i in range(num_samples):
        timestamp = base_time + timedelta(seconds=i * 5)
        scenario = chosen_scenarios[i]

        if scenario == "pristine_ethernet":
            interface = "Ethernet0"
            connection_type = "Ethernet"
            latency = float(np.random.normal(12.0, 2.5))
            packet_loss = 0.0 if np.random.rand() > 0.05 else float(np.random.uniform(0.0, 0.2))
            jitter = float(np.random.exponential(1.5))
            download_bw = float(np.random.normal(150.0, 20.0))
            upload_bw = float(np.random.normal(50.0, 10.0))
            signal_strength = None  # Explicitly None for Ethernet!
            network_util = float(np.random.uniform(5.0, 35.0))

        elif scenario == "good_wifi":
            interface = "Wi-Fi"
            connection_type = "Wi-Fi"
            latency = float(np.random.normal(25.0, 5.0))
            packet_loss = 0.0 if np.random.rand() > 0.1 else float(np.random.uniform(0.0, 0.4))
            jitter = float(np.random.exponential(3.0))
            download_bw = float(np.random.normal(75.0, 15.0))
            upload_bw = float(np.random.normal(25.0, 5.0))
            signal_strength = float(np.random.uniform(75.0, 98.0))
            network_util = float(np.random.uniform(10.0, 45.0))

        elif scenario == "edge_wifi":
            interface = "Wi-Fi"
            connection_type = "Wi-Fi"
            latency = float(np.random.normal(75.0, 20.0))
            packet_loss = float(np.random.uniform(0.5, 3.5))
            jitter = float(np.random.normal(15.0, 5.0))
            download_bw = float(np.random.normal(18.0, 6.0))
            upload_bw = float(np.random.normal(6.0, 2.0))
            signal_strength = float(np.random.uniform(35.0, 55.0))
            network_util = float(np.random.uniform(40.0, 75.0))

        elif scenario == "congested_link":
            # Bufferbloat: queues fill up, latency soars, jitter is high
            interface = "Ethernet0" if np.random.rand() > 0.5 else "Wi-Fi"
            connection_type = "Ethernet" if interface == "Ethernet0" else "Wi-Fi"
            latency = float(np.random.normal(110.0, 30.0))
            packet_loss = float(np.random.uniform(1.0, 3.8))
            jitter = float(np.random.normal(22.0, 7.0))
            download_bw = float(np.random.normal(12.0, 4.0))
            upload_bw = float(np.random.normal(4.0, 1.5))
            signal_strength = None if connection_type == "Ethernet" else float(np.random.uniform(60.0, 85.0))
            network_util = float(np.random.uniform(85.0, 99.0))

        elif scenario == "lossy_link":
            interface = "Wi-Fi"
            connection_type = "Wi-Fi"
            latency = float(np.random.normal(135.0, 35.0))
            packet_loss = float(np.random.uniform(4.5, 12.0))
            jitter = float(np.random.normal(32.0, 10.0))
            download_bw = float(np.random.normal(6.0, 3.0))
            upload_bw = float(np.random.normal(2.0, 1.0))
            signal_strength = float(np.random.uniform(25.0, 45.0))
            network_util = float(np.random.uniform(50.0, 85.0))

        else:  # severely_degraded / outage
            interface = "Ethernet0" if np.random.rand() > 0.5 else "Wi-Fi"
            connection_type = "Ethernet" if interface == "Ethernet0" else "Wi-Fi"
            latency = float(np.random.normal(240.0, 50.0))
            packet_loss = float(np.random.uniform(15.0, 60.0))
            jitter = float(np.random.normal(55.0, 15.0))
            download_bw = float(np.random.uniform(0.1, 2.5))
            upload_bw = float(np.random.uniform(0.05, 1.0))
            signal_strength = None if connection_type == "Ethernet" else float(np.random.uniform(10.0, 30.0))
            network_util = float(np.random.uniform(70.0, 100.0))

        # Enforce realistic physiological bounds
        latency = max(2.0, latency)
        packet_loss = max(0.0, min(100.0, packet_loss))
        jitter = max(0.1, jitter)
        download_bw = max(0.01, download_bw)
        upload_bw = max(0.01, upload_bw)
        network_util = max(0.0, min(100.0, network_util))

        # Derive cumulative byte/packet increments
        delta_bytes_s = int((upload_bw * 1_000_000 / 8) * 5)
        delta_bytes_r = int((download_bw * 1_000_000 / 8) * 5)
        cum_bytes_sent += delta_bytes_s
        cum_bytes_recv += delta_bytes_r

        avg_pkt_sz = 1200
        cum_pkts_sent += max(1, delta_bytes_s // avg_pkt_sz)
        cum_pkts_recv += max(1, delta_bytes_r // avg_pkt_sz)

        traffic_rate_kbs = round((delta_bytes_s + delta_bytes_r) / (5.0 * 1024.0), 2)

        # Apply documented heuristic labeling rule
        label = HeuristicLabelingConfig.assign_heuristic_label(
            latency=latency,
            packet_loss=packet_loss,
            jitter=jitter,
            download_bw=download_bw,
            network_utilization=network_util,
            signal_strength=signal_strength
        )

        record = {
            "timestamp": timestamp.isoformat(),
            "interface": interface,
            "connection_type": connection_type,
            "latency": round(latency, 2),
            "packet_loss": round(packet_loss, 2),
            "jitter": round(jitter, 2),
            "download_bandwidth": round(download_bw, 2),
            "upload_bandwidth": round(upload_bw, 2),
            "signal_strength": round(signal_strength, 1) if signal_strength is not None else np.nan,
            "bytes_sent": cum_bytes_sent,
            "bytes_received": cum_bytes_recv,
            "packets_sent": cum_pkts_sent,
            "packets_received": cum_pkts_recv,
            "traffic_rate": traffic_rate_kbs,
            "network_utilization": round(network_util, 2),
            "data_source": "synthetic_demo",
            "heuristic_quality_label": label
        }
        records.append(record)

    df = pd.DataFrame(records)

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_file, index=False)
        print(f"Generated {len(df)} samples saved to: {out_file}")
        print("Class Distribution:")
        print(df["heuristic_quality_label"].value_counts(normalize=True))

    return df


if __name__ == "__main__":
    out_csv = Path(__file__).resolve().parent / "datasets" / "network_telemetry_dataset.csv"
    generate_synthetic_telemetry_dataset(num_samples=6000, output_path=str(out_csv))
