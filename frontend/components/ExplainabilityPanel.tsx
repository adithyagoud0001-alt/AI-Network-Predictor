"use client";

import React from "react";
import { HelpCircle, CheckCircle2, AlertTriangle, Info, Sparkles, BarChart2 } from "lucide-react";
import { PredictionResult, FeatureImportance } from "@/types/network";

interface ExplainabilityPanelProps {
  prediction: PredictionResult | null;
  globalImportances?: FeatureImportance[];
}

export const ExplainabilityPanel: React.FC<ExplainabilityPanelProps> = ({
  prediction,
  globalImportances = [],
}) => {
  const factors = prediction?.explanation?.contributing_factors || [];
  const probs = prediction?.class_probabilities || { GOOD: 0.85, MODERATE: 0.1, POOR: 0.05 };
  const predictedClass = prediction?.predicted_class || "GOOD";

  return (
    <div className="bg-surface rounded-2xl border border-border p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Explainable AI: Prediction Rationale
          </h3>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
          Inference Explanation
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Decision Contributing Factors */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            Key Factors Influencing Prediction ({predictedClass})
          </h4>
          <div className="space-y-2">
            {factors.length > 0 ? (
              factors.map((factor, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-surface-raised border border-border flex items-start gap-2.5 text-xs text-slate-200"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0" />
                  <span>{factor}</span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 p-3 bg-surface-raised rounded-xl">
                Evaluating real-time telemetry parameters...
              </div>
            )}
          </div>

          {/* Model Disclaimer */}
          <div className="mt-4 p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
            <Info className="h-4 w-4 text-slate-400 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Scientific Notice:</strong> Feature contributions represent statistical pattern explanations
              extracted from the ML model, rather than absolute physical network causality.
            </span>
          </div>
        </div>

        {/* Right: Class Probability Distribution & Key Global Features */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
            <BarChart2 className="h-4 w-4 text-blue-400" />
            Multiclass Probability Distribution
          </h4>

          {/* Probability Bars */}
          <div className="space-y-3 mb-5">
            {(["GOOD", "MODERATE", "POOR"] as const).map((cls) => {
              const val = (probs[cls] ?? 0) * 100;
              const isChosen = predictedClass === cls;
              return (
                <div key={cls}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className={`font-semibold ${isChosen ? "text-white" : "text-slate-400"}`}>
                      {cls} {isChosen && "★"}
                    </span>
                    <span className="text-slate-300 font-mono">{val.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-surface-raised rounded-full h-2 overflow-hidden border border-border/50">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        cls === "GOOD" ? "bg-emerald-500" : cls === "MODERATE" ? "bg-amber-500" : "bg-red-500"
                      }`}
                      style={{ width: `${Math.max(2, val)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Top Global Feature Importances */}
          {globalImportances.length > 0 && (
            <div>
              <h5 className="text-[11px] font-semibold uppercase text-slate-400 mb-2">
                Top Global Model Feature Weights
              </h5>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                {globalImportances.slice(0, 4).map((f) => (
                  <div key={f.feature} className="p-2 rounded-lg bg-surface-raised border border-border flex justify-between">
                    <span className="text-slate-300 truncate font-mono">{f.feature.replace("_", " ")}</span>
                    <span className="text-indigo-400 font-bold ml-1">{f.importance_pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
