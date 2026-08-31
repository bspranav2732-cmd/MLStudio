'use client';

import React from 'react';
import { Settings2, Sparkles, Filter, Binary, Scale } from 'lucide-react';

interface PreprocessingPanelProps {
  missingStrategy: string;
  setMissingStrategy: (s: string) => void;
  encodingStrategy: string;
  setEncodingStrategy: (s: string) => void;
  scalingStrategy: string;
  setScalingStrategy: (s: string) => void;
}

export const PreprocessingPanel: React.FC<PreprocessingPanelProps> = ({
  missingStrategy,
  setMissingStrategy,
  encodingStrategy,
  setEncodingStrategy,
  scalingStrategy,
  setScalingStrategy,
}) => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
      <div className="flex items-center space-x-2.5 pb-4 border-b border-slate-800">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400">
          <Settings2 className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-white">4. Preprocessing Pipeline</h2>
          <p className="text-xs text-slate-400">Configure data transformation steps applied cleanly inside cross-validation splits</p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Missing Values Strategy */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Filter className="h-4 w-4 text-blue-400" />
            <label className="text-xs font-semibold text-slate-200">Missing Value Imputation</label>
          </div>
          <p className="text-[11px] text-slate-400 mb-3">Strategy for imputing absent numeric and categorical cells</p>
          <select
            value={missingStrategy}
            onChange={(e) => setMissingStrategy(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="None">None (Passthrough)</option>
            <option value="Mean">Mean Imputation</option>
            <option value="Median">Median Imputation</option>
            <option value="Most Frequent">Most Frequent (Mode)</option>
          </select>
        </div>

        {/* Categorical Encoding Strategy */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Binary className="h-4 w-4 text-purple-400" />
            <label className="text-xs font-semibold text-slate-200">Categorical Encoding</label>
          </div>
          <p className="text-[11px] text-slate-400 mb-3">Convert non-numeric columns into machine-readable numeric matrices</p>
          <select
            value={encodingStrategy}
            onChange={(e) => setEncodingStrategy(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="None">None (Passthrough)</option>
            <option value="One-Hot">One-Hot Encoding (Standard)</option>
            <option value="Ordinal">Ordinal Encoding (Integer ranks)</option>
          </select>
        </div>

        {/* Feature Scaling Strategy */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Scale className="h-4 w-4 text-emerald-400" />
            <label className="text-xs font-semibold text-slate-200">Feature Scaling & Normalization</label>
          </div>
          <p className="text-[11px] text-slate-400 mb-3">Normalize numerical feature scales and variances</p>
          <select
            value={scalingStrategy}
            onChange={(e) => setScalingStrategy(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="None">None (Unscaled Raw Values)</option>
            <option value="StandardScaler">StandardScaler (Mean=0, Std=1)</option>
            <option value="MinMaxScaler">MinMaxScaler (Bound [0, 1])</option>
            <option value="RobustScaler">RobustScaler (Median & IQR Robust)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
