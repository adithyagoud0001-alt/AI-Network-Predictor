import { NetworkTelemetry, PredictionResult, QualityClass } from "@/types/network";

export function generateSimulatedTelemetry(tick: number): {
  telemetry: NetworkTelemetry;
  prediction: PredictionResult;
} {
  // Simulate slight realistic periodic fluctuations
  const phase = (tick % 20) / 20;
  const isSpike = tick % 12 === 0;

  const latency = isSpike ? 110 + Math.random() * 20 : 18 + Math.sin(phase * Math.PI * 2) * 6 + Math.random() * 3;
  const packetLoss = isSpike ? 2.5 : Math.random() > 0.85 ? 0.3 : 0.0;
  const jitter = isSpike ? 18.0 + Math.random() * 5 : 2.0 + Math.random() * 2.5;
  const downloadBw = 85.0 + Math.cos(phase * Math.PI) * 15.0;
  const uploadBw = 28.0 + Math.sin(phase * Math.PI) * 5.0;
  const util = isSpike ? 82.0 : 25.0 + Math.random() * 10;

  const quality: QualityClass = isSpike ? "MODERATE" : "GOOD";
  const stability = isSpike ? 68.0 : Math.round(94 - latency * 0.1);

  const factors = isSpike
    ? [
        `Moderate latency (${latency.toFixed(1)} ms) observed`,
        `Transient packet delay variation (${jitter.toFixed(1)} ms)`,
      ]
    : [
        `Low round-trip latency (${latency.toFixed(1)} ms)`,
        `Negligible packet loss (${packetLoss.toFixed(1)}%)`,
        `Stable delay variation (${jitter.toFixed(1)} ms)`,
      ];

  const now = new Date().toISOString();

  const telemetry: NetworkTelemetry = {
    timestamp: now,
    interface: "Wi-Fi (Simulated)",
    connection_type: "Wi-Fi",
    latency: Math.round(latency * 10) / 10,
    min_latency: Math.round((latency - 3) * 10) / 10,
    max_latency: Math.round((latency + 8) * 10) / 10,
    packet_loss: Math.round(packetLoss * 10) / 10,
    jitter: Math.round(jitter * 10) / 10,
    rfc3550_jitter: Math.round(jitter * 0.8 * 10) / 10,
    download_bandwidth: Math.round(downloadBw * 10) / 10,
    upload_bandwidth: Math.round(uploadBw * 10) / 10,
    signal_strength: 88,
    signal_strength_dbm: -56,
    bytes_sent: 10000000 + tick * 50000,
    bytes_received: 50000000 + tick * 150000,
    packets_sent: 20000 + tick * 40,
    packets_received: 60000 + tick * 120,
    traffic_rate: Math.round(downloadBw * 120),
    network_utilization: Math.round(util * 10) / 10,
  };

  const prediction: PredictionResult = {
    timestamp: now,
    predicted_class: quality,
    confidence: isSpike ? 0.88 : 0.96,
    confidence_percentage: isSpike ? 88.0 : 96.0,
    class_probabilities: isSpike
      ? { GOOD: 0.12, MODERATE: 0.85, POOR: 0.03 }
      : { GOOD: 0.95, MODERATE: 0.04, POOR: 0.01 },
    stability_score: Math.max(0, Math.min(100, Math.round(stability))),
    stability_grade: stability >= 80 ? "EXCELLENT" : "STABLE",
    explanation: {
      predicted_class: quality,
      confidence: isSpike ? 0.88 : 0.96,
      confidence_percentage: isSpike ? 88.0 : 96.0,
      contributing_factors: factors,
      disclaimer: "Feature contributions reflect statistical model explanations and empirical thresholds.",
    },
    future_forecast: {
      horizon_seconds: 30,
      forecasted_state: quality,
      stability_trend: "STABLE",
      forecast_confidence: 0.91,
      methodology: "Linear trend extrapolation & QoS risk projection",
    },
    model_name: "Random Forest",
  };

  return { telemetry, prediction };
}
