"use client";

import React from "react";
import { Activity, Play, Square, RefreshCw, Cpu, Wifi, Globe } from "lucide-react";
import { NetworkInterfaceInfo } from "@/types/network";

interface NavbarProps {
  isConnected: boolean;
  isMonitoring: boolean;
  interfaces: NetworkInterfaceInfo[];
  selectedInterface: string;
  onSelectInterface: (name: string) => void;
  onToggleMonitoring: () => void;
  onOpenModelModal: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  isConnected,
  isMonitoring,
  interfaces,
  selectedInterface,
  onSelectInterface,
  onToggleMonitoring,
  onOpenModelModal,
  onRefresh,
  isRefreshing,
}) => {
  return (
    <header className="border-b border-border bg-surface/80 backdrop-blur sticky top-0 z-50 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Activity className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg text-white tracking-tight">AI Network Connection Predictor</h1>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-blue-500/10 text-blue-400 border border-blue-500/30">
                v1.0.0
              </span>
            </div>
            <p className="text-xs text-slate-400">Real-Time Telemetry &bull; ML Quality Inference &bull; QoS Stability</p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Interface Selector */}
          <div className="flex items-center gap-1.5 bg-surface-raised px-3 py-1.5 rounded-lg border border-border text-xs">
            <Wifi className="h-4 w-4 text-slate-400" />
            <select
              value={selectedInterface}
              onChange={(e) => onSelectInterface(e.target.value)}
              className="bg-transparent text-slate-200 outline-none cursor-pointer"
            >
              <option value="" className="bg-surface text-slate-200">Auto-Detect Interface</option>
              {interfaces.map((iface) => (
                <option key={iface.name} value={iface.name} className="bg-surface text-slate-200">
                  {iface.name} ({iface.connection_type}{iface.is_up ? " - UP" : ""})
                </option>
              ))}
            </select>
          </div>

          {/* Connection Status Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-raised border border-border text-xs">
            <div className={`h-2.5 w-2.5 rounded-full ${isConnected ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`} />
            <span className="text-slate-300 font-medium">{isConnected ? "WebSocket Live" : "Polling Mode"}</span>
          </div>

          {/* Refresh Snapshot */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-raised hover:bg-slate-700/60 border border-border text-xs font-medium text-slate-200 transition"
            title="Trigger Telemetry Cycle"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin text-blue-400" : ""}`} />
            <span>Sample Now</span>
          </button>

          {/* Monitoring Toggle */}
          <button
            onClick={onToggleMonitoring}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition shadow-sm ${
              isMonitoring
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-500/20"
            }`}
          >
            {isMonitoring ? (
              <>
                <Square className="h-3.5 w-3.5 fill-current" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Start Telemetry</span>
              </>
            )}
          </button>

          {/* ML Model Info Modal Trigger */}
          <button
            onClick={onOpenModelModal}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-xs font-medium text-indigo-300 transition"
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>ML Models & Metrics</span>
          </button>
        </div>
      </div>
    </header>
  );
};
