"use client";

import React from "react";
import { AlertCircle, AlertTriangle, Info, BellRing } from "lucide-react";
import { DegradationAlert } from "@/types/network";
import { formatTime } from "@/lib/utils";

interface AlertsBannerProps {
  alerts: DegradationAlert[];
}

export const AlertsBanner: React.FC<AlertsBannerProps> = ({ alerts }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl px-4 py-3 flex items-center justify-between text-xs text-emerald-300">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-semibold">Network Telemetry Nominal:</span>
          <span className="text-emerald-400/80">No active network degradation or bufferbloat alerts detected.</span>
        </div>
        <span className="text-[11px] text-emerald-400/60 font-mono">Continuous Early Warning Active</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert, idx) => {
        const isCritical = alert.severity === "CRITICAL";
        const isWarning = alert.severity === "WARNING";

        return (
          <div
            key={idx}
            className={`rounded-xl border p-3.5 flex items-start gap-3 text-xs shadow-lg transition ${
              isCritical
                ? "bg-red-950/40 border-red-500/50 text-red-200"
                : isWarning
                ? "bg-amber-950/40 border-amber-500/50 text-amber-200"
                : "bg-blue-950/40 border-blue-500/50 text-blue-200"
            }`}
          >
            {isCritical ? (
              <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
            ) : isWarning ? (
              <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
            ) : (
              <Info className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
            )}

            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-bold tracking-tight text-white flex items-center gap-2">
                  <span>{alert.title}</span>
                  <span
                    className={`text-[10px] uppercase px-1.5 py-0.2 rounded font-bold ${
                      isCritical ? "bg-red-500/20 text-red-300" : "bg-amber-500/20 text-amber-300"
                    }`}
                  >
                    {alert.severity}
                  </span>
                </span>
                <span suppressHydrationWarning className="text-[11px] text-slate-400 font-mono">
                  {formatTime(alert.timestamp)}
                </span>
              </div>
              <p className="mt-1 text-slate-300 leading-relaxed">{alert.message}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
