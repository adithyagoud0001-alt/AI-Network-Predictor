"use client";

import React from "react";
import { ShieldCheck, AlertTriangle, AlertOctagon, TrendingUp, TrendingDown, Clock, Radio } from "lucide-react";
import { PredictionResult, QualityClass } from "@/types/network";
import { getQualityColors, formatTime } from "@/lib/utils";

interface StatusHeaderProps {
  prediction: PredictionResult | null;
  interfaceName: string;
  connectionType: string;
  timestamp: string;
}

export const StatusHeader: React.FC<StatusHeaderProps> = ({
  prediction,
  interfaceName,
  connectionType,
  timestamp,
}) => {
  const qualityClass: QualityClass = prediction?.predicted_class || "GOOD";
  const colors = getQualityColors(qualityClass);
  const stability = prediction?.stability_score ?? 100;
  const confidence = prediction?.confidence_percentage ?? 95;
  const grade = prediction?.stability_grade ?? "STABLE";
  const forecast = prediction?.future_forecast;

  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => {
    setMounted(true);
  }, []);

  const renderStatusIcon = () => {
    switch (qualityClass) {
      case "GOOD":
        return <ShieldCheck className="h-10 w-10 text-emerald-400 animate-pulse" />;
      case "MODERATE":
        return <AlertTriangle className="h-10 w-10 text-amber-400" />;
      case "POOR":
        return <AlertOctagon className="h-10 w-10 text-red-400 animate-bounce" />;
    }
  };

  return (
    <div className="bg-surface rounded-2xl border border-border p-6 shadow-xl relative overflow-hidden">
      {/* Background ambient gradient glow */}
      <div
        className={`absolute -right-20 -top-20 w-80 h-80 rounded-full blur-3xl opacity-20 pointer-events-none ${
          qualityClass === "GOOD" ? "bg-emerald-500" : qualityClass === "MODERATE" ? "bg-amber-500" : "bg-red-500"
        }`}
      />

      <div className="relative z-10 grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Main Status Block */}
        <div className="md:col-span-5 flex items-center gap-5 border-b md:border-b-0 md:border-r border-border pb-6 md:pb-0 md:pr-6">
          <div className={`p-4 rounded-2xl border ${colors.border} ${colors.bg} ${colors.glow}`}>
            {renderStatusIcon()}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Network Connection Status
              </span>
              <span className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-surface-raised text-slate-300 border border-border">
                <Radio className="h-3 w-3 text-blue-400" />
                {connectionType} &bull; {interfaceName}
              </span>
            </div>
            <div className={`text-4xl font-extrabold tracking-tight ${colors.text}`}>
              {qualityClass}
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
              <Clock className="h-3.5 w-3.5" />
              <span suppressHydrationWarning>
                {mounted && timestamp ? `Sampled at ${formatTime(timestamp)}` : "Live telemetry"}
              </span>
            </div>
          </div>
        </div>

        {/* Stability Score Card */}
        <div className="md:col-span-3 border-b md:border-b-0 md:border-r border-border pb-6 md:pb-0 md:pr-6">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Stability Score
            </span>
            <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${
              stability >= 80 ? "bg-emerald-500/20 text-emerald-300" : stability >= 60 ? "bg-amber-500/20 text-amber-300" : "bg-red-500/20 text-red-300"
            }`}>
              {grade}
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white">{stability}</span>
            <span className="text-sm text-slate-400">/ 100</span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-surface-raised rounded-full h-2 mt-2.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                stability >= 80 ? "bg-emerald-500" : stability >= 60 ? "bg-amber-500" : "bg-red-500"
              }`}
              style={{ width: `${Math.max(5, stability)}%` }}
            />
          </div>
        </div>

        {/* Prediction Confidence & Model */}
        <div className="md:col-span-2 border-b md:border-b-0 md:border-r border-border pb-6 md:pb-0 md:pr-6">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
            Prediction Confidence
          </span>
          <div className="text-3xl font-extrabold text-white">
            {confidence.toFixed(1)}%
          </div>
          <span className="text-xs text-slate-400 mt-1 block">
            Model: <span className="text-indigo-400 font-medium">{prediction?.model_name || "Random Forest"}</span>
          </span>
        </div>

        {/* 30-Second Near-Term Horizon Forecast (Section 13) */}
        <div className="md:col-span-2">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              +30s Horizon
            </span>
            {forecast?.stability_trend === "DEGRADING" ? (
              <TrendingDown className="h-3.5 w-3.5 text-red-400" />
            ) : forecast?.stability_trend === "IMPROVING" ? (
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
            ) : (
              <span className="h-2 w-2 rounded-full bg-slate-400" />
            )}
          </div>
          <div className="text-xl font-bold text-slate-200">
            {forecast?.forecasted_state || qualityClass}
          </div>
          <span className={`text-[11px] font-medium block mt-0.5 ${
            forecast?.stability_trend === "DEGRADING" ? "text-red-400" : forecast?.stability_trend === "IMPROVING" ? "text-emerald-400" : "text-slate-400"
          }`}>
            Trend: {forecast?.stability_trend || "STABLE"}
          </span>
        </div>
      </div>
    </div>
  );
};
