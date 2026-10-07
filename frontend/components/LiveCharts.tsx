"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
} from "recharts";
import { NetworkTelemetry } from "@/types/network";
import { formatTime } from "@/lib/utils";

interface LiveChartsProps {
  history: NetworkTelemetry[];
  stabilityHistory: { timestamp: string; score: number }[];
}

export const LiveCharts: React.FC<LiveChartsProps> = ({ history, stabilityHistory }) => {
  const chartData = history.map((item, idx) => ({
    time: formatTime(item.timestamp),
    latency: item.latency,
    jitter: item.jitter,
    packet_loss: item.packet_loss,
    download: item.download_bandwidth,
    upload: item.upload_bandwidth,
    stability: stabilityHistory[idx]?.score ?? 95,
  }));

  const darkTooltipStyle = {
    backgroundColor: "#111827",
    borderColor: "#1f293d",
    color: "#f8fafc",
    borderRadius: "0.5rem",
    fontSize: "12px",
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 1. Latency & Jitter Chart */}
      <div className="bg-surface rounded-2xl border border-border p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Latency & Jitter Dynamics
            </h3>
            <p className="text-xs text-slate-400">Round-trip time (RTT) & Packet Delay Variation (ms)</p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-blue-400 font-medium">
              <span className="h-2 w-2 rounded-full bg-blue-400" /> Latency
            </span>
            <span className="flex items-center gap-1.5 text-purple-400 font-medium">
              <span className="h-2 w-2 rounded-full bg-purple-400" /> Jitter
            </span>
          </div>
        </div>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} unit="ms" />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Line type="monotone" dataKey="latency" stroke="#38bdf8" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="jitter" stroke="#c084fc" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. Packet Loss Chart */}
      <div className="bg-surface rounded-2xl border border-border p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Packet Loss Percentage
            </h3>
            <p className="text-xs text-slate-400">Droprate impact on TCP retransmissions (%)</p>
          </div>
          <span className="text-xs text-rose-400 font-medium flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-400" /> Loss %
          </span>
        </div>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} unit="%" domain={[0, "auto"]} />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Area type="monotone" dataKey="packet_loss" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#lossGradient)" isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Bandwidth / Throughput Chart */}
      <div className="bg-surface rounded-2xl border border-border p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Throughput Rates
            </h3>
            <p className="text-xs text-slate-400">Download & Upload transfer rates (Mbps)</p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-cyan-400 font-medium">
              <span className="h-2 w-2 rounded-full bg-cyan-400" /> Download
            </span>
            <span className="flex items-center gap-1.5 text-indigo-400 font-medium">
              <span className="h-2 w-2 rounded-full bg-indigo-400" /> Upload
            </span>
          </div>
        </div>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} unit="M" />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Line type="monotone" dataKey="download" stroke="#22d3ee" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="upload" stroke="#818cf8" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. Stability Score Over Time */}
      <div className="bg-surface rounded-2xl border border-border p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Network Stability Score Index
            </h3>
            <p className="text-xs text-slate-400">Continuous QoS health score (0 - 100)</p>
          </div>
          <span className="text-xs text-emerald-400 font-medium flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400" /> Score Index
          </span>
        </div>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="stabilityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} domain={[0, 100]} />
              <Tooltip contentStyle={darkTooltipStyle} />
              <Area type="monotone" dataKey="stability" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#stabilityGradient)" isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
