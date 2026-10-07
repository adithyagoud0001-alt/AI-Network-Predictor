"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Navbar } from "@/components/Navbar";
import { StatusHeader } from "@/components/StatusHeader";
import { MetricCards } from "@/components/MetricCards";
import { LiveCharts } from "@/components/LiveCharts";
import { ExplainabilityPanel } from "@/components/ExplainabilityPanel";
import { AlertsBanner } from "@/components/AlertsBanner";
import { ModelEvaluationModal } from "@/components/ModelEvaluationModal";
import { NetworkSimulator } from "@/components/NetworkSimulator";
import { HistoricalTable } from "@/components/HistoricalTable";
import {
  NetworkTelemetry,
  PredictionResult,
  DegradationAlert,
  NetworkInterfaceInfo,
  ModelMetadata,
  WebSocketTelemetryMessage,
} from "@/types/network";
import { API_BASE, WS_BASE } from "@/lib/config";
import { generateSimulatedTelemetry } from "@/lib/simulator";

export default function DashboardPage() {
  const [telemetry, setTelemetry] = useState<NetworkTelemetry | null>(null);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [history, setHistory] = useState<NetworkTelemetry[]>([]);
  const [stabilityHistory, setStabilityHistory] = useState<{ timestamp: string; score: number }[]>([]);
  const [alerts, setAlerts] = useState<DegradationAlert[]>([]);
  const [interfaces, setInterfaces] = useState<NetworkInterfaceInfo[]>([]);
  const [selectedInterface, setSelectedInterface] = useState<string>("");
  const [isMonitoring, setIsMonitoring] = useState<boolean>(true);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);
  const [modelMetadata, setModelMetadata] = useState<ModelMetadata | null>(null);
  const [isModelModalOpen, setIsModelModalOpen] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const simTickRef = useRef<number>(0);

  // 1. Fetch initial interfaces and model metadata
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [ifaceRes, modelRes] = await Promise.all([
          fetch(`${API_BASE}/network/interfaces`),
          fetch(`${API_BASE}/model/info`),
        ]);
        if (ifaceRes.ok) {
          const ifaces = await ifaceRes.json();
          setInterfaces(ifaces);
        }
        if (modelRes.ok) {
          const meta = await modelRes.json();
          setModelMetadata(meta);
        }
      } catch (err) {
        console.warn("Initial API load notice:", err);
      }
    };
    fetchInitialData();
  }, []);

  // 2. Fallback HTTP Poll function
  const pollData = useCallback(async () => {
    try {
      const [curRes, predRes, alertRes] = await Promise.all([
        fetch(`${API_BASE}/network/current`),
        fetch(`${API_BASE}/prediction/latest`),
        fetch(`${API_BASE}/alerts`),
      ]);

      if (curRes.ok) {
        const telem: NetworkTelemetry = await curRes.json();
        setTelemetry(telem);
        setHistory((prev) => [...prev.slice(-30), telem]);
        setServerError(null);
        setIsDemoMode(false);
      }

      if (predRes.ok) {
        const pred: PredictionResult = await predRes.json();
        setPrediction(pred);
        setStabilityHistory((prev) => [
          ...prev.slice(-30),
          { timestamp: pred.timestamp || new Date().toISOString(), score: pred.stability_score },
        ]);
      }

      if (alertRes.ok) {
        const alertData = await alertRes.json();
        setAlerts(alertData.active_alerts || []);
      }
    } catch (err) {
      // Backend not running (e.g. running standalone on Vercel)
      // Gracefully switch to simulated telemetry so the dashboard remains 100% interactive!
      setIsDemoMode(true);
      simTickRef.current += 1;
      const sim = generateSimulatedTelemetry(simTickRef.current);
      setTelemetry(sim.telemetry);
      setPrediction(sim.prediction);
      setHistory((prev) => [...prev.slice(-30), sim.telemetry]);
      setStabilityHistory((prev) => [
        ...prev.slice(-30),
        { timestamp: sim.telemetry.timestamp, score: sim.prediction.stability_score },
      ]);
      setServerError(null);
    }
  }, []);

  // 3. WebSocket Real-Time Connection with automatic reconnect & fallback
  useEffect(() => {
    let ws: WebSocket | null = null;
    let fallbackInterval: NodeJS.Timeout | null = null;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(WS_BASE);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          setServerError(null);
        };

        ws.onmessage = (event) => {
          try {
            const data: WebSocketTelemetryMessage = JSON.parse(event.data);
            if (data.type === "telemetry_update") {
              if (data.telemetry) {
                setTelemetry(data.telemetry);
                setHistory((prev) => [...prev.slice(-30), data.telemetry]);
              }
              if (data.prediction) {
                setPrediction(data.prediction);
                setStabilityHistory((prev) => [
                  ...prev.slice(-30),
                  { timestamp: data.telemetry?.timestamp || new Date().toISOString(), score: data.prediction.stability_score },
                ]);
              }
              if (data.alerts) {
                setAlerts(data.alerts);
              }
            }
          } catch (e) {
            console.error("Error parsing WebSocket frame:", e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          // Fallback to polling when socket closes
          if (!fallbackInterval) {
            fallbackInterval = setInterval(pollData, 4000);
          }
          // Retry socket after 5s
          setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = () => {
          setIsConnected(false);
        };
      } catch (err) {
        setIsConnected(false);
        if (!fallbackInterval) {
          fallbackInterval = setInterval(pollData, 4000);
        }
      }
    };

    connectWebSocket();
    // Immediate initial poll
    pollData();

    return () => {
      if (ws) ws.close();
      if (fallbackInterval) clearInterval(fallbackInterval);
    };
  }, [pollData]);

  // 4. Interface selection handler
  const handleSelectInterface = async (name: string) => {
    setSelectedInterface(name);
    try {
      const url = name ? `${API_BASE}/network/interface/select?interface_name=${encodeURIComponent(name)}` : `${API_BASE}/network/interface/select`;
      await fetch(url, { method: "POST" });
      handleManualRefresh();
    } catch (e) {
      console.error(e);
    }
  };

  // 5. Toggle monitoring
  const handleToggleMonitoring = async () => {
    try {
      const action = isMonitoring ? "stop" : "start";
      await fetch(`${API_BASE}/monitoring/${action}`, { method: "POST" });
      setIsMonitoring(!isMonitoring);
    } catch (e) {
      console.error(e);
    }
  };

  // 6. Manual snapshot trigger
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetch(`${API_BASE}/network/collect-now`, { method: "POST" });
      await pollData();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Navbar */}
      <Navbar
        isConnected={isConnected}
        isMonitoring={isMonitoring}
        interfaces={interfaces}
        selectedInterface={selectedInterface}
        onSelectInterface={handleSelectInterface}
        onToggleMonitoring={handleToggleMonitoring}
        onOpenModelModal={() => setIsModelModalOpen(true)}
        onRefresh={handleManualRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-6">
        {/* Cloud Demo Mode Notification Banner (Active when no cloud/local backend is connected) */}
        {isDemoMode && (
          <div className="bg-blue-950/30 border border-blue-500/30 rounded-xl p-3 text-xs text-blue-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="font-semibold">Cloud Simulation Active:</span>
              <span className="text-blue-300/80">
                Displaying real-time simulated network telemetry. Start your local backend (run_backend.bat) or set NEXT_PUBLIC_API_URL to bind to physical network adapters.
              </span>
            </div>
            <span className="text-[11px] font-mono text-cyan-400/80 bg-blue-900/40 px-2 py-0.5 rounded border border-blue-500/30 self-start sm:self-auto">
              Client-Side QoS Engine
            </span>
          </div>
        )}

        {/* Real-Time Early Warning & Degradation Alerts Banner */}
        <AlertsBanner alerts={alerts} />

        {/* Primary Status Card (GOOD / MODERATE / POOR + Stability + Confidence + 30s Forecast) */}
        <StatusHeader
          prediction={prediction}
          interfaceName={telemetry?.interface || selectedInterface || "Auto"}
          connectionType={telemetry?.connection_type || "Network Interface"}
          timestamp={telemetry?.timestamp || ""}
        />

        {/* Six Core Metric Cards */}
        <MetricCards telemetry={telemetry} />

        {/* Live Recharts Observability Dashboard (Latency, Loss, Bandwidth, Stability) */}
        <LiveCharts history={history} stabilityHistory={stabilityHistory} />

        {/* Explainability Panel (Contributing Factors, Probabilities, Feature Importance) */}
        <ExplainabilityPanel
          prediction={prediction}
          globalImportances={modelMetadata?.global_feature_importances}
        />

        {/* Interactive "What-If" QoS Simulator (Coursework Lab Demonstrator) */}
        <NetworkSimulator />

        {/* Chronological Telemetry & Prediction Stream Table */}
        <HistoricalTable
          history={history}
          predictions={{}}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-surface/50 py-6 px-4 text-center text-xs text-slate-500">
        <p>AI-Based Network Connection Predictor &bull; Computer Networks Final Project</p>
        <p className="mt-1 text-[11px] text-slate-600">
          OS-Aware Network Telemetry &bull; RFC 3550 Jitter Metric &bull; Scikit-Learn Multiclass Pipeline &bull; FastAPI &bull; Next.js &bull; Recharts
        </p>
      </footer>

      {/* Modal: Model Evaluation & Comparison Benchmark */}
      <ModelEvaluationModal
        isOpen={isModelModalOpen}
        onClose={() => setIsModelModalOpen(false)}
        metadata={modelMetadata}
      />
    </div>
  );
}
