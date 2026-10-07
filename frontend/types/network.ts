export type QualityClass = "GOOD" | "MODERATE" | "POOR";

export interface NetworkTelemetry {
  timestamp: string;
  interface: string;
  connection_type: string;
  latency: number;
  min_latency?: number | null;
  max_latency?: number | null;
  packet_loss: number;
  jitter: number;
  rfc3550_jitter?: number | null;
  download_bandwidth: number;
  upload_bandwidth: number;
  signal_strength: number | null;
  signal_strength_dbm?: number | null;
  bytes_sent: number;
  bytes_received: number;
  packets_sent: number;
  packets_received: number;
  traffic_rate: number;
  network_utilization: number;
}

export interface PredictionExplanation {
  predicted_class: QualityClass;
  confidence: number;
  confidence_percentage: number;
  contributing_factors: string[];
  disclaimer: string;
}

export interface FutureForecast {
  horizon_seconds: number;
  forecasted_state: QualityClass;
  stability_trend: "STABLE" | "DEGRADING" | "IMPROVING";
  forecast_confidence: number;
  methodology: string;
}

export interface PredictionResult {
  timestamp?: string;
  predicted_class: QualityClass;
  confidence: number;
  confidence_percentage: number;
  class_probabilities: Record<string, number>;
  stability_score: number;
  stability_grade: "EXCELLENT" | "STABLE" | "DEGRADED" | "CRITICAL";
  explanation: PredictionExplanation;
  future_forecast?: FutureForecast | null;
  model_name: string;
}

export interface DegradationAlert {
  timestamp: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  title: string;
  message: string;
  metric?: string;
  current_value?: number;
  threshold?: number;
  trend_direction?: string;
}

export interface NetworkInterfaceInfo {
  name: string;
  is_up: boolean;
  speed_mbps: number | null;
  mtu: number | null;
  addresses: string[];
  connection_type: string;
  is_default: boolean;
}

export interface ModelValidationMetric {
  model_name: string;
  train_duration_sec: number;
  cv_macro_f1_mean: number;
  cv_macro_f1_std: number;
  val_accuracy: number;
  val_macro_f1: number;
  val_macro_precision: number;
  val_macro_recall: number;
  val_weighted_f1: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
  importance_pct: number;
}

export interface ModelMetadata {
  model_version: string;
  timestamp: string;
  champion_model_name: string;
  classes: string[];
  input_features: string[];
  validation_comparison: ModelValidationMetric[];
  champion_test_metrics: {
    accuracy: number;
    macro_precision: number;
    macro_recall: number;
    macro_f1: number;
    confusion_matrix: number[][];
    classes: string[];
  };
  global_feature_importances: FeatureImportance[];
}

export interface WebSocketTelemetryMessage {
  type: string;
  telemetry: NetworkTelemetry;
  prediction: PredictionResult;
  alerts: DegradationAlert[];
}
