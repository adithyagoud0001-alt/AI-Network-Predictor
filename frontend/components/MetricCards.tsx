"use client";

import React from "react";
import { Gauge, Percent, Waves, ArrowDownCircle, ArrowUpCircle, Wifi, BarChart3 } from "lucide-react";
import { NetworkTelemetry } from "@/types/network";

interface MetricCardsProps {
  telemetry: NetworkTelemetry | null;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ telemetry }) => {
  const latency = telemetry?.latency ?? 0;
  const packetLoss = telemetry?.packet_loss ?? 0;
  const jitter = telemetry?.jitter ?? 0;
  const rfcJitter = telemetry?.rfc3550_jitter ?? 0;
  const downloadBw = telemetry?.download_bandwidth ?? 0;
  const uploadBw = telemetry?.upload_bandwidth ?? 0;
  const signalStrength = telemetry?.signal_strength;
  const trafficRate = telemetry?.traffic_rate ?? 0;
  const utilization = telemetry?.network_utilization ?? 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {/* 1. Latency Card */}
      <div className="bg-surface rounded-xl border border-border p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase">Latency</span>
          <Gauge className="h-4 w-4 text-blue-400" />
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-white">{latency.toFixed(1)}</span>
          <span className="text-xs text-slate-400">ms</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
          <span>Min: {telemetry?.min_latency?.toFixed(1) ?? "--"} ms</span>
          <span>Max: {telemetry?.max_latency?.toFixed(1) ?? "--"} ms</span>
        </div>
      </div>

      {/* 2. Packet Loss Card */}
      <div className="bg-surface rounded-xl border border-border p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase">Packet Loss</span>
          <Percent className="h-4 w-4 text-rose-400" />
        </div>
        <div className="flex items-baseline gap-1">
          <span className={`text-2xl font-bold ${packetLoss > 2 ? "text-red-400" : "text-white"}`}>
            {packetLoss.toFixed(1)}
          </span>
          <span className="text-xs text-slate-400">%</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          Status: <span className={packetLoss === 0 ? "text-emerald-400" : packetLoss < 2 ? "text-amber-400" : "text-red-400"}>
            {packetLoss === 0 ? "Zero Loss" : packetLoss < 2 ? "Acceptable" : "Elevated"}
          </span>
        </div>
      </div>

      {/* 3. Jitter Card */}
      <div className="bg-surface rounded-xl border border-border p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase">Jitter (PDV)</span>
          <Waves className="h-4 w-4 text-purple-400" />
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-white">{jitter.toFixed(1)}</span>
          <span className="text-xs text-slate-400">ms</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          RFC 3550: <span className="text-purple-300 font-medium">{rfcJitter.toFixed(1)} ms</span>
        </div>
      </div>

      {/* 4. Bandwidth Card */}
      <div className="bg-surface rounded-xl border border-border p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase">Throughput</span>
          <div className="flex gap-1">
            <ArrowDownCircle className="h-3.5 w-3.5 text-cyan-400" />
            <ArrowUpCircle className="h-3.5 w-3.5 text-indigo-400" />
          </div>
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-white">{downloadBw.toFixed(1)}</span>
          <span className="text-xs text-slate-400">Mbps &darr;</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          Upload: <span className="text-indigo-300 font-medium">{uploadBw.toFixed(1)} Mbps &uarr;</span>
        </div>
      </div>

      {/* 5. Signal Strength Card */}
      <div className="bg-surface rounded-xl border border-border p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase">Signal RSSI</span>
          <Wifi className="h-4 w-4 text-amber-400" />
        </div>
        <div className="flex items-baseline gap-1">
          {signalStrength !== null && signalStrength !== undefined ? (
            <>
              <span className="text-2xl font-bold text-white">{signalStrength.toFixed(0)}</span>
              <span className="text-xs text-slate-400">%</span>
            </>
          ) : (
            <span className="text-lg font-semibold text-slate-400">Ethernet</span>
          )}
        </div>
        <div className="text-[11px] text-slate-400 mt-1 truncate">
          {signalStrength !== null && signalStrength !== undefined
            ? `${telemetry?.signal_strength_dbm ?? "--"} dBm`
            : "Wired (N/A)"}
        </div>
      </div>

      {/* 6. Traffic & Utilization Card */}
      <div className="bg-surface rounded-xl border border-border p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase">Utilization</span>
          <BarChart3 className="h-4 w-4 text-emerald-400" />
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-white">{utilization.toFixed(1)}</span>
          <span className="text-xs text-slate-400">%</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          Rate: <span className="text-emerald-300 font-medium">{trafficRate.toFixed(0)} KB/s</span>
        </div>
      </div>
    </div>
  );
};
