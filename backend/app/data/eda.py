"""Exploratory Data Analysis (EDA) Module

Performs rigorous statistical and exploratory analysis on network telemetry data:
- Missing value audit (including validation of Ethernet RSSI null-handling)
- Summary statistics & skewness
- Outlier detection using IQR
- Cross-feature correlation matrix
- Class balance evaluation across GOOD, MODERATE, and POOR
- Generates JSON summary and visualization figures.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


def run_eda(dataset_path: str, output_dir: str) -> Dict[str, Any]:
    """Runs end-to-end EDA on the network dataset."""
    df = pd.read_csv(dataset_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    numeric_cols = [
        "latency", "packet_loss", "jitter", "download_bandwidth",
        "upload_bandwidth", "traffic_rate", "network_utilization"
    ]
    # signal_strength is analyzed separately due to expected structural NaNs on Ethernet

    # 1. Dataset Shape and Missing Value Analysis
    missing_counts = df.isnull().sum().to_dict()
    missing_pct = (df.isnull().sum() / len(df) * 100).round(2).to_dict()

    # Verify Ethernet signal_strength null handling
    ethernet_rows = df[df["connection_type"] == "Ethernet"]
    wifi_rows = df[df["connection_type"] == "Wi-Fi"]
    ethernet_nan_pct = (ethernet_rows["signal_strength"].isnull().sum() / max(1, len(ethernet_rows))) * 100
    wifi_nan_pct = (wifi_rows["signal_strength"].isnull().sum() / max(1, len(wifi_rows))) * 100

    # 2. Class Balance
    class_counts = df["heuristic_quality_label"].value_counts().to_dict()
    class_proportions = (df["heuristic_quality_label"].value_counts(normalize=True) * 100).round(2).to_dict()

    # 3. Descriptive Statistics
    desc_stats = df[numeric_cols].describe().round(2).to_dict()

    # 4. Outlier Analysis using IQR (1.5 * IQR)
    outlier_counts = {}
    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        outlier_counts[col] = {
            "count": int(len(outliers)),
            "percentage": round(float(len(outliers) / len(df) * 100), 2),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2)
        }

    # 5. Correlation Matrix
    corr = df[numeric_cols].corr().round(3)
    corr_dict = corr.to_dict()

    # 6. Plotting and Artifact Generation
    # A. Correlation Heatmap
    plt.figure(figsize=(9, 7))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
    plt.title("Network Telemetry Correlation Matrix")
    plt.tight_layout()
    corr_plot_path = out_dir / "correlation_matrix.png"
    plt.savefig(corr_plot_path, dpi=150)
    plt.close()

    # B. Class Distribution Bar Chart
    plt.figure(figsize=(7, 4.5))
    colors = ["#22c55e", "#ef4444", "#f59e0b"]  # Good (green), Poor (red), Moderate (amber)
    order = ["GOOD", "MODERATE", "POOR"]
    counts = [class_counts.get(k, 0) for k in order]
    bars = plt.bar(order, counts, color=["#10b981", "#f59e0b", "#ef4444"], edgecolor="#333", width=0.5)
    plt.title("Heuristic Quality Class Distribution")
    plt.ylabel("Sample Count")
    plt.xlabel("Quality Class")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 30, f"{yval} ({yval/len(df)*100:.1f}%)", ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    class_plot_path = out_dir / "class_distribution.png"
    plt.savefig(class_plot_path, dpi=150)
    plt.close()

    eda_summary = {
        "total_samples": len(df),
        "total_features": len(df.columns),
        "class_distribution": class_counts,
        "class_percentages": class_proportions,
        "missing_values": {
            "counts": missing_counts,
            "percentages": missing_pct,
            "ethernet_signal_nan_percentage": round(ethernet_nan_pct, 2),
            "wifi_signal_nan_percentage": round(wifi_nan_pct, 2)
        },
        "outlier_analysis": outlier_counts,
        "descriptive_statistics": desc_stats,
        "correlations": corr_dict,
        "generated_artifacts": {
            "correlation_matrix_png": str(corr_plot_path),
            "class_distribution_png": str(class_plot_path)
        }
    }

    report_json_path = out_dir / "eda_report.json"
    with open(report_json_path, "w") as f:
        json.dump(eda_summary, f, indent=2)

    print(f"EDA Completed Successfully. Summary written to: {report_json_path}")
    return eda_summary


if __name__ == "__main__":
    csv_file = Path(__file__).resolve().parent / "datasets" / "network_telemetry_dataset.csv"
    out_folder = Path(__file__).resolve().parent / "datasets"
    run_eda(str(csv_file), str(out_folder))
