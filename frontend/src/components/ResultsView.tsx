'use client';

import React, { useState } from 'react';
import { Award, Info, Sparkles, Check, Plus, BarChart3, Table as TableIcon } from 'lucide-react';
import { ExperimentResults, api } from '../lib/api';
import { formatMetric } from '../lib/utils';

interface ResultsViewProps {
  results: ExperimentResults;
}

export const ResultsView: React.FC<ResultsViewProps> = ({ results }) => {
  const [isAdding, setIsAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const handleAddToComparison = async () => {
    setIsAdding(true);
    try {
      await api.addToComparison(results.job_id);
      setAdded(true);
      setTimeout(() => setAdded(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setIsAdding(false);
    }
  };

  const isRegression = results.problem_type === 'Regression';
  const metrics = results.metrics || {};
  const evalConfig = results.evaluation_config || {};

  return (
    <div className="space-y-6">
      {/* 1. Evaluation Protocol Badge */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-sm">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Info className="h-4 w-4 text-blue-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Evaluation Protocol</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">Trained in {results.training_time}s</span>
        </div>

        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-slate-400">Validation:</span>
            <p className="font-semibold text-white mt-0.5">{evalConfig.validation || 'N/A'}</p>
          </div>
          <div>
            <span className="text-slate-400">Optimization:</span>
            <p className="font-semibold text-amber-400 mt-0.5">{evalConfig.optimization || 'None'}</p>
          </div>
          <div>
            <span className="text-slate-400">Random State:</span>
            <p className="font-mono text-slate-200 mt-0.5">{evalConfig.random_state ?? 42}</p>
          </div>
          <div>
            <span className="text-slate-400">Random Forest OOB:</span>
            <p className="font-semibold text-slate-200 mt-0.5">
              {evalConfig.oob ? (
                <span className="text-emerald-400 font-semibold">Enabled (Score: {formatMetric(evalConfig.oob_score)})</span>
              ) : (
                'Disabled'
              )}
            </p>
          </div>
        </div>

        {results.best_params && Object.keys(results.best_params).length > 0 && (
          <div className="mt-4 rounded-xl bg-slate-950/60 p-3.5 border border-slate-800">
            <span className="text-xs font-semibold text-amber-400">Optimized Best Parameters:</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {Object.entries(results.best_params).map(([k, v]) => (
                <span key={k} className="rounded-md bg-amber-500/10 px-2.5 py-1 text-xs font-mono text-amber-300 border border-amber-500/20">
                  {k}: <strong className="text-white">{String(v)}</strong>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 2. Metrics Cards */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-bold text-white">Evaluation Metrics ({evalConfig.validation || 'Test Set'})</h3>
          <button
            type="button"
            onClick={handleAddToComparison}
            disabled={isAdding || added}
            className="flex items-center space-x-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-blue-500 transition-colors disabled:bg-emerald-600"
          >
            {added ? (
              <>
                <Check className="h-3.5 w-3.5" />
                <span>Added to Comparison!</span>
              </>
            ) : (
              <>
                <Plus className="h-3.5 w-3.5" />
                <span>Add Run to Comparison</span>
              </>
            )}
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {isRegression ? (
            <>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">R² Score</span>
                <p className="mt-2 text-2xl font-black text-blue-400 font-mono">
                  {formatMetric(metrics['R2 Score'])}
                </p>
                <span className="text-[11px] text-slate-400">Coefficient of Determination</span>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">RMSE</span>
                <p className="mt-2 text-2xl font-black text-indigo-400 font-mono">
                  {formatMetric(metrics['RMSE'])}
                </p>
                <span className="text-[11px] text-slate-400">Root Mean Squared Error</span>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">MAE</span>
                <p className="mt-2 text-2xl font-black text-purple-400 font-mono">
                  {formatMetric(metrics['MAE'])}
                </p>
                <span className="text-[11px] text-slate-400">Mean Absolute Error</span>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">MAPE</span>
                <p className="mt-2 text-2xl font-black text-emerald-400 font-mono">
                  {formatMetric(metrics['MAPE'], true)}
                </p>
                <span className="text-[11px] text-slate-400">Mean Absolute Percentage Error</span>
              </div>
            </>
          ) : (
            <>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Accuracy</span>
                <p className="mt-2 text-2xl font-black text-blue-400 font-mono">
                  {formatMetric(metrics['Accuracy'], true)}
                </p>
                <span className="text-[11px] text-slate-400">Overall Classification Accuracy</span>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Precision</span>
                <p className="mt-2 text-2xl font-black text-indigo-400 font-mono">
                  {formatMetric(metrics['Precision'], true)}
                </p>
                <span className="text-[11px] text-slate-400">Weighted Average Precision</span>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Recall</span>
                <p className="mt-2 text-2xl font-black text-purple-400 font-mono">
                  {formatMetric(metrics['Recall'], true)}
                </p>
                <span className="text-[11px] text-slate-400">Weighted Average Recall</span>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">F1 Score</span>
                <p className="mt-2 text-2xl font-black text-emerald-400 font-mono">
                  {formatMetric(metrics['F1 Score'], true)}
                </p>
                <span className="text-[11px] text-slate-400">Harmonic Mean of Precision & Recall</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* 3. Feature Importance (if model supports it) */}
      {results.feature_importances && results.feature_importances.length > 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
          <div className="flex items-center space-x-2 pb-4 border-b border-slate-800 mb-4">
            <BarChart3 className="h-4 w-4 text-blue-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Feature Importance Hierarchy</h3>
          </div>

          <div className="space-y-2.5">
            {results.feature_importances.slice(0, 10).map((item, idx) => {
              const maxImp = results.feature_importances[0].importance || 1;
              const pct = Math.round((item.importance / maxImp) * 100);
              return (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-200">{item.feature}</span>
                    <span className="font-mono text-blue-400">{(item.importance * 100).toFixed(2)}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-blue-600 to-indigo-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Prediction Preview Table */}
      {results.predictions_preview && results.predictions_preview.length > 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
            <div className="flex items-center space-x-2">
              <TableIcon className="h-4 w-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Predictions Sample</h3>
            </div>
            <span className="text-xs text-slate-400">First 20 Validation Predictions</span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60 max-h-64">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="sticky top-0 bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-4 py-2">#</th>
                  <th className="px-4 py-2">Actual</th>
                  <th className="px-4 py-2">Predicted</th>
                  {isRegression ? <th className="px-4 py-2">Residual</th> : <th className="px-4 py-2">Confidence</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {results.predictions_preview.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-800/30">
                    <td className="px-4 py-1.5 font-mono text-slate-500">{i + 1}</td>
                    <td className="px-4 py-1.5 font-mono font-medium text-slate-200">
                      {typeof row.Actual === 'number' ? row.Actual.toFixed(4) : String(row.Actual)}
                    </td>
                    <td className="px-4 py-1.5 font-mono font-medium text-blue-400">
                      {typeof row.Predicted === 'number' ? row.Predicted.toFixed(4) : String(row.Predicted)}
                    </td>
                    <td className="px-4 py-1.5 font-mono text-slate-400">
                      {row.Residual !== undefined ? Number(row.Residual).toFixed(4) : row.Probability !== undefined ? `${(Number(row.Probability) * 100).toFixed(1)}%` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
