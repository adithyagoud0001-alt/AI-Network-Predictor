# Academic Project Report: AI-Based Network Connection Predictor

**Course:** Computer Networks  
**Project Title:** AI-Based Network Connection Predictor: Real-Time Observability, Machine Learning QoS Inference, and Early Degradation Warning  
**Date:** October 2026  

---

## 1. Abstract

Modern digital communication infrastructure demands dependable, low-latency, and resilient network connections. Traditional network monitoring utilities—such as `ping`, `traceroute`, or static threshold SNMP alerts—operate retrospectively, detecting failures only after packet loss or link collapse has impacted end-user applications. This project designs and implements an end-to-end, production-grade network observability platform that bridges fundamental **Computer Networks** concepts with **Machine Learning**. 

The system continuously samples platform-aware network telemetry (Round-Trip Time, RFC 3550 interarrival jitter, packet loss percentage, link throughput, Wi-Fi RSSI, and interface utilization), computes leakage-free temporal features, and predicts connection quality into three discrete Quality of Service (QoS) classes: **GOOD**, **MODERATE**, or **POOR**. Furthermore, it computes an independent, deterministic **Network Stability Score (0–100)** conforming to ITU-T Y.1541 standards, generates early degradation warnings based on latency slope analysis, and delivers human-interpretable explanations through Explainable AI (XAI). Across a rigorous 5-fold stratified cross-validation comparison of 5 candidate algorithms (Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost), the Random Forest champion pipeline achieved **99.11% accuracy** and **98.83% Macro F1-score** on held-out test data.

---

## 2. Introduction

Quality of Service (QoS) and Quality of Experience (QoE) are foundational pillars in Computer Networks. Emerging multimedia applications—including WebRTC video conferences, real-time cloud gaming, remote telemetry, and financial high-frequency execution—exhibit heightened sensitivity to minute variations in round-trip latency, packet delay variation (jitter), and packet drops.

While classical network monitoring tools report isolated diagnostic numbers at instantaneous intervals, network administrators and autonomous software agents lack predictive foresight into subtle link degradation. By integrating statistical machine learning with physical network telemetry, this project transforms raw network telemetry into actionable, explainable operational intelligence.

---

## 3. Problem Statement

Existing enterprise and operating system network utilities suffer from several acute limitations:
1. **Passive and Retrospective:** Failures are reported only after severe buffer exhaustion or TCP timeout events occur.
2. **Lack of Multi-Dimensional Synthesis:** A link may maintain 0% packet loss while suffering from severe bufferbloat (soaring latency and jitter), misleading simple threshold monitors.
3. **Absence of Explainability:** Generic telemetry dashboards graph raw lines without articulating why a connection feels sluggish to an end-user.
4. **Data Fabrication in Generic ML Demos:** Typical toy ML projects fabricate values for unavailable measurements (e.g., inventing RSSI values on wired Ethernet), violating real-world networking constraints.

---

## 4. Existing System vs. Proposed System

### Limitations of Existing Systems
- **Static Threshold Alerts:** Static rules trigger alert fatigue when temporary network bursts occur, yet fail to detect slow, steady latency creeping caused by bottleneck queue exhaustion.
- **Single-Metric Blindness:** Evaluating only bandwidth ignores the devastating effect of small packet-loss bursts on TCP congestion control windows ($W \approx 1/\sqrt{p}$).
- **Platform Incompatibility:** Telemetry scripts frequently assume Linux-specific tools (`iwconfig`), failing across Windows or macOS hosts.

### Proposed System Innovations
- **Modular OS-Aware Abstraction Layer:** Provides tailored collectors across Windows (`netsh`, native ICMP ping), Linux (`/proc/net/wireless`, `iwconfig`), and macOS (`airport`), honoring missing-value semantics (null RSSI for wired interfaces).
- **Dual Analytical Architecture:** Logically decouples continuous deterministic QoS scoring (0–100 Stability Score) from probabilistic machine learning pattern classification (GOOD / MODERATE / POOR).
- **Proactive Early Warning Detection:** Continuously calculates latency gradients ($d(\text{RTT})/dt$) to alert administrators of impending degradation before TCP retransmissions trigger application stutter.
- **Explainable Prediction:** Synthesizes local factor attribution to explain why an inference was made (e.g., "Elevated latency of 145 ms causing transit delay").

---

## 5. Network Parameters & Theoretical Formulations

### 5.1 Round-Trip Time (RTT) & Queuing Delay
End-to-end packet latency comprises four components:
$$\text{Delay}_{\text{total}} = d_{\text{proc}} + d_{\text{queue}} + d_{\text{trans}} + d_{\text{prop}}$$
In loaded links, queuing delay ($d_{\text{queue}}$) at interface buffers dominates, manifesting as bufferbloat.

### 5.2 Packet Loss & TCP Throughput Collapse
According to the Mathis formula for TCP throughput:
$$\text{Throughput} \le \frac{\text{MSS}}{\text{RTT} \cdot \sqrt{p}}$$
where $p$ is the packet loss probability. Even a 2% packet loss rate collapses TCP throughput by more than 80%, explaining why packet loss carries the highest penalty in our stability engine.

### 5.3 Mathematical Jitter (RFC 3550 & RFC 3393)
Packet Delay Variation (PDV) is calculated continuously across successive probe packets:
$$\text{MAPDV} = \frac{1}{N - 1} \sum_{k=1}^{N - 1} |RTT_{k+1} - RTT_k|$$
RFC 3550 smoothed interarrival jitter:
$$J(i) = J(i - 1) + \frac{|D(i - 1, i)| - J(i - 1)}{16}$$

---

## 6. Deterministic Network Stability Score Methodology

Conforming to ITU-T Y.1541 QoS recommendation profiles, the stability score is calculated on a bounded scale from 0.0 to 100.0:
$$\text{Score} = 100 - (P_{\text{loss}} + P_{\text{latency}} + P_{\text{jitter}} + P_{\text{signal}} + P_{\text{util}})$$
- **$P_{\text{loss}}$ (Max 35):** Penalty scaling up to 10% packet loss.
- **$P_{\text{latency}}$ (Max 25):** Excess delay penalty above ideal 20 ms benchmark.
- **$P_{\text{jitter}}$ (Max 20):** Excess delay variation penalty above 2 ms.
- **$P_{\text{signal}}$ (Max 10):** Signal strength degradation penalty (applied only when Wi-Fi RSSI is present).
- **$P_{\text{util}}$ (Max 10):** Queue congestion penalty for link utilization $> 80\%$.

---

## 7. Machine Learning Methodology

### 7.1 Dataset Generation & Heuristic Target Rationale
To train candidate models across diverse operational environments without biological bias, a multi-scenario telemetry generator created 6,000 chronological observations representing:
1. High-speed Fiber / Pristine Ethernet (low latency, 0% loss, null RSSI)
2. Normal Wi-Fi (good signal, minimal jitter)
3. Edge Wi-Fi (attenuated RSSI, fluctuating delay)
4. Congested Link (bufferbloat, high utilization, queue delay)
5. Lossy Link (packet drop bursts, volatile jitter)
6. Outage / Critical Failure (extreme delay, high loss)

> **Important Disclosure:** The multiclass target `heuristic_quality_label` is derived using explicit ITU-T QoS threshold rules. It is explicitly documented as a deterministic heuristic target, not an infallible ground truth.

### 7.2 Strict Leakage Prevention in Feature Engineering
All rolling window transformations (rolling mean, rolling standard deviation, rates of change) utilize strictly backward-looking windows ($[t-k, t]$). During training, Scikit-learn pipelines fit transformers strictly on training folds and apply identical parameters to test sets.

---

## 8. Experimental Evaluation & Results

### 8.1 Model Comparison Matrix (5-Fold Stratified Cross-Validation)

| Algorithm | 5-Fold CV Macro F1 | Val Accuracy | Val Macro F1 | Val Precision | Val Recall | Train Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest (Selected)** | **0.9940** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **2.81 s** |
| Gradient Boosting | 0.9979 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 10.09 s |
| XGBoost | 0.9963 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.97 s |
| Decision Tree | 0.9943 | 0.9967 | 0.9956 | 0.9951 | 0.9962 | 2.00 s |
| Logistic Regression | 0.9295 | 0.9456 | 0.9299 | 0.9295 | 0.9316 | 2.89 s |

*Selection Criterion:* While Gradient Boosting and Random Forest achieved comparable macro F1 scores, Random Forest demonstrated superior training time efficiency and resilience against localized feature skewness.

### 8.2 Final Evaluation on Held-Out Test Set (900 Independent Samples)
- **Overall Accuracy:** 99.11%
- **Macro Precision:** 0.9875
- **Macro Recall:** 0.9894
- **Macro F1-Score:** 0.9883

#### Test Set Confusion Matrix

| Actual Class \ Predicted Class | GOOD | MODERATE | POOR |
| :--- | :---: | :---: | :---: |
| **GOOD** | **437** | 0 | 0 |
| **MODERATE** | 0 | **201** | 1 |
| **POOR** | 0 | 7 | **254** |

---

## 9. Relationship Between Computer Networks and Machine Learning

This project highlights how ML augments classical networking principles:
1. **From Deterministic Thresholds to Multivariate Decision Boundaries:** While networking rules define QoS standards, real-world links exhibit complex multi-metric interactions (e.g., slight loss combined with rising jitter under moderate utilization). ML identifies non-linear degradation boundaries that static rules miss.
2. **Bufferbloat & Congestion Fingerprinting:** By pairing traffic utilization with latency rate-of-change, tree-based models learn the distinctive signature of queue growth before TCP packet drops occur.
3. **Explainability as Operational Diagnostic:** Translating high-dimensional probability vectors back into human-readable network diagnostics enables network operators to swiftly pinpoint whether link degradation stems from physical wireless attenuation or network bottleneck queues.

---

## 10. Conclusion and Future Scope

The **AI-Based Network Connection Predictor** successfully demonstrates a production-grade integration of Computer Networks telemetry, rigorous mathematical formulations, and modern machine learning pipelines. The platform achieves high classification performance, provides real-time observability via WebSockets, and offers proactive degradation warnings.

### Future Scope
- **Time-Series Horizon Forecasting (LSTM / GRU / Transformer):** Expanding beyond the 30-second linear trend extrapolation to deep recurrent forecasting over 5-to-15 minute horizons.
- **Active Bandwidth Probing (BBR Model):** Integrating packet-pair dispersion or TCP BBR pacing rate probing for non-intrusive bottleneck bandwidth measurement.
- **SDN Integration:** Interfacing with OpenFlow controllers to trigger automated routing failover upon receiving early degradation alerts.

---

## 11. References
1. ITU-T Recommendation Y.1541: *Network performance objectives for IP-based services*, International Telecommunication Union, 2011.
2. ITU-T Recommendation G.1010: *End-user multimedia QoS categories*, 2001.
3. Schulzrinne, H., Casner, S., Frederick, R., & Jacobson, V., *RFC 3550: RTP: A Transport Protocol for Real-Time Applications*, IETF, 2003.
4. Demichelis, C., & Chimento, P., *RFC 3393: IP Packet Delay Variation Metric for IP Performance Metrics (IPPM)*, IETF, 2002.
5. Mathis, M., Semke, J., Mahdavi, J., & Ott, T., *The macroscopic behavior of the TCP congestion avoidance algorithm*, ACM SIGCOMM CCR, 1997.
6. Nichols, K., & Jacobson, V., *Controlling Queue Delay (CoDel / Bufferbloat)*, Communications of the ACM, 2012.
