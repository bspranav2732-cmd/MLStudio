'use client';

import React from 'react';
import { Target, HelpCircle } from 'lucide-react';
import { DatasetInfo } from '../lib/api';

interface TargetSelectorProps {
  dataset: DatasetInfo;
  target: string;
  setTarget: (target: string) => void;
  targetUnit: string;
  setTargetUnit: (unit: string) => void;
  problemType: 'Regression' | 'Classification';
  setProblemType: (type: 'Regression' | 'Classification') => void;
}

export const TargetSelector: React.FC<TargetSelectorProps> = ({
  dataset,
  target,
  setTarget,
  targetUnit,
  setTargetUnit,
  problemType,
  setProblemType,
}) => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
      <div className="flex items-center space-x-2.5 pb-4 border-b border-slate-800">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400">
          <Target className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-white">2. Target & Task Definition</h2>
          <p className="text-xs text-slate-400">Select the dependent target variable and task formulation</p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-3">
        {/* Target Column Dropdown */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Target Variable (Y)
          </label>
          <select
            value={target}
            onChange={(e) => {
              const selected = e.target.value;
              setTarget(selected);
              // Auto-detect problem type if numeric or categorical
              const colMeta = dataset.columns.find((c) => c.name === selected);
              if (colMeta) {
                if (!colMeta.is_numeric || colMeta.unique <= 10) {
                  // Suggest classification if low unique count or non-numeric
                  setProblemType(colMeta.is_numeric && colMeta.unique > 15 ? 'Regression' : 'Classification');
                } else {
                  setProblemType('Regression');
                }
              }
            }}
            className="w-full rounded-xl border border-slate-700 bg-slate-800 px-3.5 py-2.5 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="" disabled>Select Target Column...</option>
            {dataset.columns.map((col) => (
              <option key={col.name} value={col.name}>
                {col.name} ({col.type}) {col.unique} unique
              </option>
            ))}
          </select>
        </div>

        {/* Problem Type Toggle */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Modeling Task Type
          </label>
          <div className="flex rounded-xl bg-slate-800 p-1 border border-slate-700">
            <button
              type="button"
              onClick={() => setProblemType('Regression')}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                problemType === 'Regression'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Regression
            </button>
            <button
              type="button"
              onClick={() => setProblemType('Classification')}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                problemType === 'Classification'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Classification
            </button>
          </div>
        </div>

        {/* Target Unit Label */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Unit Label (Optional, for plots)
          </label>
          <input
            type="text"
            placeholder="e.g. MPa, kg, %, USD"
            value={targetUnit}
            onChange={(e) => setTargetUnit(e.target.value)}
            className="w-full rounded-xl border border-slate-700 bg-slate-800 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  );
};
