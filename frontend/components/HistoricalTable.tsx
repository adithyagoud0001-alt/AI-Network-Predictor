"use client";

import React from "react";
import { History, ArrowRight } from "lucide-react";
import { NetworkTelemetry, QualityClass } from "@/types/network";
import { formatTime, getQualityColors } from "@/lib/utils";

interface HistoricalTableProps {
  history: NetworkTelemetry[];
  predictions: Record<number, QualityClass>;
}

export const HistoricalTable: React.FC<HistoricalTableProps> = ({
  history,
  predictions,
}) => {
  return (
    <div className="bg-surface rounded-2xl border border-border p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-blue-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Historical Telemetry & Prediction Timeline
          </h3>
        </div>
        <span className="text-xs text-slate-400">Chronological Telemetry Stream</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-surface-raised border-b border-border text-slate-400 font-semibold uppercase text-[10px]">
            <tr>
              <th className="py-2.5 px-3">Time</th>
              <th className="py-2.5 px-3">Quality Prediction</th>
              <th className="py-2.5 px-3">Interface</th>
              <th className="py-2.5 px-3">Latency</th>
              <th className="py-2.5 px-3">Packet Loss</th>
              <th className="py-2.5 px-3">Jitter</th>
              <th className="py-2.5 px-3">Download</th>
              <th className="py-2.5 px-3">Signal</th>
              <th className="py-2.5 px-3">Utilization</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {history.slice(-15).reverse().map((item, idx) => {
              const quality: QualityClass = predictions[idx] || (
                item.packet_loss > 3 || item.latency > 140 ? "POOR" : item.packet_loss > 0.5 || item.latency > 60 ? "MODERATE" : "GOOD"
              );
              const colors = getQualityColors(quality);

              return (
                <tr key={idx} className="hover:bg-slate-900/40 transition">
                  <td suppressHydrationWarning className="py-2.5 px-3 font-mono text-slate-300">{formatTime(item.timestamp)}</td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] border ${colors.bg} ${colors.text} ${colors.border}`}>
                      {quality}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-300 font-mono text-[11px]">{item.interface}</td>
                  <td className="py-2.5 px-3 text-white font-semibold font-mono">{item.latency.toFixed(1)} ms</td>
                  <td className={`py-2.5 px-3 font-mono ${item.packet_loss > 1 ? "text-red-400 font-bold" : "text-slate-300"}`}>
                    {item.packet_loss.toFixed(1)}%
                  </td>
                  <td className="py-2.5 px-3 text-purple-300 font-mono">{item.jitter.toFixed(1)} ms</td>
                  <td className="py-2.5 px-3 text-cyan-300 font-mono">{item.download_bandwidth.toFixed(1)} Mbps</td>
                  <td className="py-2.5 px-3 text-slate-400 font-mono">
                    {item.signal_strength !== null ? `${item.signal_strength}%` : "Ethernet"}
                  </td>
                  <td className="py-2.5 px-3 text-slate-300 font-mono">{item.network_utilization.toFixed(1)}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
