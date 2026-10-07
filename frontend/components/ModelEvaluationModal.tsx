"use client";

import React from "react";
import { X, Award, CheckCircle, Database, GitBranch, Cpu } from "lucide-react";
import { ModelMetadata } from "@/types/network";

interface ModelEvaluationModalProps {
  isOpen: boolean;
  onClose: () => void;
  metadata: ModelMetadata | null;
}

export const ModelEvaluationModal: React.FC<ModelEvaluationModalProps> = ({
  isOpen,
  onClose,
  metadata,
}) => {
  if (!isOpen) return null;

  const comparison = metadata?.validation_comparison || [];
  const champion = metadata?.champion_model_name || "Random Forest";
  const testMetrics = metadata?.champion_test_metrics;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-surface border border-border w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-raised">
          <div className="flex items-center gap-2.5">
            <Cpu className="h-5 w-5 text-indigo-400" />
            <div>
              <h2 className="text-base font-bold text-white">Machine Learning Model Evaluation & Comparison</h2>
              <p className="text-xs text-slate-400">Computer Networks Course Project &bull; Multiclass Classification Analysis</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-300">
          {/* Champion Banner */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-blue-900/40 border border-indigo-500/40 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-indigo-500/20 text-indigo-300">
                <Award className="h-6 w-6" />
              </div>
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                  Selected Champion Model
                </span>
                <h3 className="text-lg font-extrabold text-white">{champion}</h3>
                <p className="text-xs text-slate-300">
                  Selected objectively via 5-Fold Cross-Validation and held-out validation Macro F1 score.
                </p>
              </div>
            </div>
            {testMetrics && (
              <div className="text-right">
                <span className="text-xs text-slate-400 block">Held-Out Test Accuracy</span>
                <span className="text-2xl font-black text-emerald-400">
                  {(testMetrics.accuracy * 100).toFixed(2)}%
                </span>
                <span className="text-[11px] text-slate-400 block">Macro F1: {(testMetrics.macro_f1 * 100).toFixed(2)}%</span>
              </div>
            )}
          </div>

          {/* Model Comparison Table */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-blue-400" />
              Algorithm Performance Benchmark (5-Fold Stratified CV & Validation Set)
            </h4>
            <div className="overflow-x-auto border border-border rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-raised border-b border-border text-slate-400 font-semibold uppercase text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Model</th>
                    <th className="py-2.5 px-3">CV Macro F1</th>
                    <th className="py-2.5 px-3">Val Accuracy</th>
                    <th className="py-2.5 px-3">Val Macro F1</th>
                    <th className="py-2.5 px-3">Val Precision</th>
                    <th className="py-2.5 px-3">Val Recall</th>
                    <th className="py-2.5 px-3">Train Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {comparison.map((m) => {
                    const isWinner = m.model_name === champion;
                    return (
                      <tr key={m.model_name} className={isWinner ? "bg-indigo-950/20 font-semibold" : "hover:bg-slate-900/50"}>
                        <td className="py-2.5 px-3 flex items-center gap-1.5 text-white">
                          {isWinner && <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />}
                          <span>{m.model_name}</span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-300">{(m.cv_macro_f1_mean * 100).toFixed(2)}%</td>
                        <td className="py-2.5 px-3 font-mono text-slate-300">{(m.val_accuracy * 100).toFixed(2)}%</td>
                        <td className={`py-2.5 px-3 font-mono font-bold ${isWinner ? "text-emerald-400" : "text-slate-200"}`}>
                          {(m.val_macro_f1 * 100).toFixed(2)}%
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-300">{(m.val_macro_precision * 100).toFixed(2)}%</td>
                        <td className="py-2.5 px-3 font-mono text-slate-300">{(m.val_macro_recall * 100).toFixed(2)}%</td>
                        <td className="py-2.5 px-3 font-mono text-slate-400">{m.train_duration_sec}s</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Confusion Matrix */}
          {testMetrics?.confusion_matrix && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                <Database className="h-4 w-4 text-purple-400" />
                Held-Out Test Set Confusion Matrix (Rows = Actual, Columns = Predicted)
              </h4>
              <div className="p-4 bg-surface-raised rounded-xl border border-border inline-block min-w-full">
                <div className="grid grid-cols-4 gap-2 text-center text-xs font-mono">
                  <div className="font-bold text-slate-400 text-left">Actual \ Pred</div>
                  <div className="font-bold text-emerald-400">GOOD</div>
                  <div className="font-bold text-amber-400">MODERATE</div>
                  <div className="font-bold text-red-400">POOR</div>

                  {testMetrics.confusion_matrix.map((row, rIdx) => {
                    const rowName = ["GOOD", "MODERATE", "POOR"][rIdx];
                    return (
                      <React.Fragment key={rIdx}>
                        <div className="font-bold text-slate-300 text-left py-1.5">{rowName}</div>
                        {row.map((val, cIdx) => (
                          <div
                            key={cIdx}
                            className={`py-1.5 rounded font-semibold ${
                              rIdx === cIdx ? "bg-emerald-900/40 text-emerald-300 border border-emerald-500/30" : "bg-slate-900/50 text-slate-400"
                            }`}
                          >
                            {val}
                          </div>
                        ))}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border bg-surface-raised flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-medium text-xs transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
