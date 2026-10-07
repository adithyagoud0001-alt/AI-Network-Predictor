"""Network Stability Score Calculation Engine

Provides a standardized, normalized network stability score (0 to 100)
derived from fundamental network Quality of Service (QoS) principles
(ITU-T G.1010 and ITU-T Y.1541 standards).

IMPORTANT ARCHITECTURAL DISTINCTION:
The Network Stability Score is an analytical, deterministic QoS metric.
It is logically and mathematically independent of the ML classification model.
Both are presented side-by-side to provide operational transparency:
- ML Prediction: Probability-driven pattern classifier (GOOD, MODERATE, POOR)
- Stability Score: Continuous deterministic health index (0 - 100)
"""

from typing import Optional, Dict, Any


class NetworkStabilityEngine:
    """Calculates continuous network stability scores based on penalty functions."""

    # Reference QoS benchmarks based on ITU-T Y.1541 Class 0 / Class 1
    IDEAL_LATENCY_MS: float = 20.0
    MAX_TOLERABLE_LATENCY_MS: float = 250.0

    IDEAL_JITTER_MS: float = 2.0
    MAX_TOLERABLE_JITTER_MS: float = 50.0

    MAX_TOLERABLE_PACKET_LOSS_PCT: float = 10.0

    MIN_DESIRED_BANDWIDTH_MBPS: float = 25.0

    @classmethod
    def calculate_score(
        cls,
        latency: float,
        packet_loss: float,
        jitter: float,
        download_bandwidth: float,
        upload_bandwidth: float,
        network_utilization: float,
        signal_strength: Optional[float] = None
    ) -> float:
        """Calculates a normalized 0-100 Network Stability Score.

        Penalty Weight Distribution (Total max penalty = 100):
        - Packet Loss: Up to 35 points penalty (most severe impact on transport layer)
        - Latency (RTT): Up to 25 points penalty
        - Jitter (Delay Variation): Up to 20 points penalty
        - Signal Strength (if Wi-Fi): Up to 10 points penalty
        - Network Utilization / Congestion: Up to 10 points penalty

        Returns:
            Float score between 0.0 (catastrophic) and 100.0 (flawless).
        """
        score = 100.0

        # 1. Packet Loss Penalty (Weight: 35)
        # Loss > 10% completely exhausts packet loss penalty
        loss_capped = min(packet_loss, cls.MAX_TOLERABLE_PACKET_LOSS_PCT)
        loss_penalty = (loss_capped / cls.MAX_TOLERABLE_PACKET_LOSS_PCT) * 35.0
        # Exponential curve for severe loss
        if packet_loss > 1.0:
            loss_penalty = min(35.0, loss_penalty * 1.2)
        score -= loss_penalty

        # 2. Latency Penalty (Weight: 25)
        if latency > cls.IDEAL_LATENCY_MS:
            excess_latency = min(latency - cls.IDEAL_LATENCY_MS, cls.MAX_TOLERABLE_LATENCY_MS - cls.IDEAL_LATENCY_MS)
            latency_penalty = (excess_latency / (cls.MAX_TOLERABLE_LATENCY_MS - cls.IDEAL_LATENCY_MS)) * 25.0
            score -= latency_penalty

        # 3. Jitter Penalty (Weight: 20)
        if jitter > cls.IDEAL_JITTER_MS:
            excess_jitter = min(jitter - cls.IDEAL_JITTER_MS, cls.MAX_TOLERABLE_JITTER_MS - cls.IDEAL_JITTER_MS)
            jitter_penalty = (excess_jitter / (cls.MAX_TOLERABLE_JITTER_MS - cls.IDEAL_JITTER_MS)) * 20.0
            score -= jitter_penalty

        # 4. Signal Strength Penalty (Weight: 10, applicable to Wi-Fi)
        if signal_strength is not None:
            # If Wi-Fi signal < 70%, penalize
            if signal_strength < 70.0:
                deficit = (70.0 - max(0.0, signal_strength)) / 70.0
                signal_penalty = deficit * 10.0
                score -= signal_penalty
        else:
            # For Ethernet / null RSSI, no signal penalty applied
            pass

        # 5. Network Utilization & Throughput Congestion Penalty (Weight: 10)
        if network_utilization > 80.0:
            util_penalty = ((network_utilization - 80.0) / 20.0) * 10.0
            score -= util_penalty

        # Boundary clamping to [0.0, 100.0]
        final_score = max(0.0, min(100.0, score))
        return round(final_score, 1)

    @classmethod
    def get_score_breakdown(
        cls,
        latency: float,
        packet_loss: float,
        jitter: float,
        download_bandwidth: float,
        upload_bandwidth: float,
        network_utilization: float,
        signal_strength: Optional[float] = None
    ) -> Dict[str, Any]:
        """Provides transparent sub-component breakdown of the stability score."""
        score = cls.calculate_score(
            latency=latency,
            packet_loss=packet_loss,
            jitter=jitter,
            download_bandwidth=download_bandwidth,
            upload_bandwidth=upload_bandwidth,
            network_utilization=network_utilization,
            signal_strength=signal_strength
        )

        grade = "EXCELLENT" if score >= 85 else ("STABLE" if score >= 70 else ("DEGRADED" if score >= 45 else "CRITICAL"))

        return {
            "stability_score": score,
            "grade": grade,
            "metrics": {
                "latency_ms": latency,
                "packet_loss_pct": packet_loss,
                "jitter_ms": jitter,
                "signal_strength_pct": signal_strength,
                "network_utilization_pct": network_utilization,
                "download_bandwidth_mbps": download_bandwidth,
                "upload_bandwidth_mbps": upload_bandwidth
            }
        }
