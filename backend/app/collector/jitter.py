"""Network Jitter Calculation Module

This module implements mathematically rigorous calculations of packet delay variation (jitter)
following standard network engineering specifications, specifically RFC 3550 (RTP: A Transport
Protocol for Real-Time Applications) and RFC 3393 (IP Packet Delay Variation Metric).

Mathematical Definitions:
1. Packet Delay Variation (PDV / Inter-sample Jitter):
   Given a sequence of round-trip times (RTT) or one-way transit delays [d_1, d_2, ..., d_N]:
   Difference: D(i, j) = d_j - d_i

2. Mean Absolute Packet Delay Variation (MAPDV):
   MAPDV = (1 / (N - 1)) * SUM_{k=1}^{N-1} |d_{k+1} - d_k|

3. RFC 3550 Statistical Jitter (Smoothed Interarrival Jitter):
   J(0) = 0
   J(i) = J(i - 1) + (|D(i-1, i)| - J(i - 1)) / 16

Handling Missing / Lost Samples:
- If a ping packet is dropped, it does not have a finite RTT.
- Dropped packets are counted towards packet loss percentage.
- For jitter calculation, delay differences are calculated only between consecutive
  successfully received packets.
- If fewer than 2 packets are received successfully, jitter is defined as 0.0 ms
  (or undefined/insufficient data).
"""

from typing import List, Optional, Tuple
import math
import numpy as np


class JitterCalculator:
    """Calculates network jitter using multiple standard network telemetry formulations."""

    @staticmethod
    def calculate_rfc3550_jitter(delays_ms: List[float]) -> float:
        """Computes RFC 3550 exponential moving average jitter.
        
        Formula:
            J(i) = J(i-1) + (|d_i - d_{i-1}| - J(i-1)) / 16
        
        Args:
            delays_ms: List of successfully measured packet delays/RTTs in milliseconds.
            
        Returns:
            Smoothed jitter in milliseconds (rounded to 3 decimal places).
        """
        valid_delays = [d for d in delays_ms if d is not None and not math.isnan(d) and d >= 0]
        if len(valid_delays) < 2:
            return 0.0

        jitter = 0.0
        for i in range(1, len(valid_delays)):
            diff = abs(valid_delays[i] - valid_delays[i - 1])
            jitter += (diff - jitter) / 16.0

        return round(jitter, 3)

    @staticmethod
    def calculate_mean_pdv(delays_ms: List[float]) -> float:
        """Computes Mean Absolute Packet Delay Variation (MAPDV).
        
        Formula:
            MAPDV = (1 / (N - 1)) * sum(|d_{k+1} - d_k|)
            
        Args:
            delays_ms: List of successfully measured packet delays in milliseconds.
            
        Returns:
            Mean delay variation in milliseconds.
        """
        valid_delays = [d for d in delays_ms if d is not None and not math.isnan(d) and d >= 0]
        if len(valid_delays) < 2:
            return 0.0

        diffs = [abs(valid_delays[i] - valid_delays[i - 1]) for i in range(1, len(valid_delays))]
        return round(float(np.mean(diffs)), 3)

    @staticmethod
    def calculate_std_jitter(delays_ms: List[float]) -> float:
        """Computes the sample standard deviation of delay measurements.
        
        Args:
            delays_ms: List of successfully measured packet delays in milliseconds.
            
        Returns:
            Sample standard deviation in milliseconds.
        """
        valid_delays = [d for d in delays_ms if d is not None and not math.isnan(d) and d >= 0]
        if len(valid_delays) < 2:
            return 0.0
        return round(float(np.std(valid_delays, ddof=1)), 3)

    @classmethod
    def compute_all_metrics(cls, delays_ms: List[Optional[float]]) -> Tuple[float, float, float]:
        """Convenience method returning (rfc3550_jitter, mean_pdv, std_dev)."""
        valid = [d for d in delays_ms if d is not None and not math.isnan(d) and d >= 0]
        if len(valid) < 2:
            return 0.0, 0.0, 0.0
        return (
            cls.calculate_rfc3550_jitter(valid),
            cls.calculate_mean_pdv(valid),
            cls.calculate_std_jitter(valid)
        )
