'use client';

import React, { useState, useEffect } from 'react';
import { Layers, Trash2, RefreshCw, Trophy, ArrowRight } from 'lucide-react';
import { api } from '../lib/api';
import { formatMetric } from '../lib/utils';

export const ComparisonView: React.FC = () => {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await api.getComparison();
      setRuns(data.runs || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleClear = async () => {
    try {
      await api.clearComparison();
      setRuns([]);
    } catch (err) {
      console.error(err);
    }
  };

  if (runs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-800 text-slate-400 mb-3">
          <Layers className="h-6 w-6" />
        </div>
        <h3 className="text-sm font-semibold text-white">No Models in Comparison List</h3>
        <p className="mt-1 text-xs text-slate-400 max-w-sm">
          Run an experiment and click <strong>"Add Run to Comparison"</strong> to compare multiple model architectures side-by-side.
        </p>
      </div>
    );
  }

  // Extract all metric keys
  const metricKeys = Array.from(
    new Set(runs.flatMap((r) => Object.keys(r.metrics || {})))
  );

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
        <div className="flex items-center space-x-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
            <Trophy className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Model Architecture Benchmark & Comparison</h2>
            <p className="text-xs text-slate-400">Evaluating {runs.length} trained models across identical experimental criteria</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleClear}
          className="flex items-center space-x-1.5 rounded-lg bg-rose-500/10 px-3 py-1.5 text-xs font-medium text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 transition-colors"
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span>Clear All Comparison Runs</span>
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Task</th>
              <th className="px-4 py-3">Validation</th>
              <th className="px-4 py-3">Optimization</th>
              <th className="px-4 py-3">Training Time</th>
              {metricKeys.map((k) => (
                <th key={k} className="px-4 py-3">{k}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {runs.map((run, idx) => (
              <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-3 font-semibold text-white">{run.model_name}</td>
                <td className="px-4 py-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded ${run.problem_type === 'Regression' ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'}`}>
                    {run.problem_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400">{run.split_method || 'Train-Test'}</td>
                <td className="px-4 py-3 text-amber-400">{run.optimization || 'None'}</td>
                <td className="px-4 py-3 font-mono text-slate-400">{run.training_time?.toFixed(2)}s</td>
                {metricKeys.map((k) => (
                  <td key={k} className="px-4 py-3 font-mono font-bold text-blue-400">
                    {formatMetric(run.metrics?.[k])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
