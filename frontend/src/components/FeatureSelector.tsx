'use client';

import React from 'react';
import { SlidersHorizontal, CheckSquare, Square, Check } from 'lucide-react';
import { DatasetInfo } from '../lib/api';

interface FeatureSelectorProps {
  dataset: DatasetInfo;
  target: string;
  selectedFeatures: string[];
  setSelectedFeatures: (features: string[]) => void;
}

export const FeatureSelector: React.FC<FeatureSelectorProps> = ({
  dataset,
  target,
  selectedFeatures,
  setSelectedFeatures,
}) => {
  const availableColumns = dataset.columns.filter((c) => c.name !== target);

  const handleSelectAll = () => {
    setSelectedFeatures(availableColumns.map((c) => c.name));
  };

  const handleDeselectAll = () => {
    setSelectedFeatures([]);
  };

  const toggleFeature = (name: string) => {
    if (selectedFeatures.includes(name)) {
      setSelectedFeatures(selectedFeatures.filter((f) => f !== name));
    } else {
      setSelectedFeatures([...selectedFeatures, name]);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
            <SlidersHorizontal className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">3. Feature Selection (X)</h2>
            <p className="text-xs text-slate-400">Choose independent features to include in the training pipeline</p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleSelectAll}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700 transition-colors"
          >
            Select All
          </button>
          <button
            type="button"
            onClick={handleDeselectAll}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700 transition-colors"
          >
            Clear All
          </button>
          <span className="rounded-lg bg-blue-500/10 px-3 py-1.5 text-xs font-semibold text-blue-400 border border-blue-500/20">
            {selectedFeatures.length} of {availableColumns.length} Selected
          </span>
        </div>
      </div>

      {/* Feature Grid Checkboxes */}
      <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
        {availableColumns.map((col) => {
          const isSelected = selectedFeatures.includes(col.name);
          return (
            <div
              key={col.name}
              onClick={() => toggleFeature(col.name)}
              className={`flex cursor-pointer items-center justify-between rounded-xl border p-3 transition-all duration-150 ${
                isSelected
                  ? 'border-blue-500/60 bg-blue-500/10 text-white shadow-sm'
                  : 'border-slate-800 bg-slate-800/40 text-slate-400 hover:border-slate-700 hover:bg-slate-800/80 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center space-x-2.5 overflow-hidden">
                <div
                  className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${
                    isSelected
                      ? 'border-blue-500 bg-blue-600 text-white'
                      : 'border-slate-600 bg-slate-900'
                  }`}
                >
                  {isSelected && <Check className="h-3 w-3" />}
                </div>
                <span className="truncate text-xs font-medium">{col.name}</span>
              </div>

              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                  col.is_numeric
                    ? 'bg-blue-500/20 text-blue-300'
                    : 'bg-purple-500/20 text-purple-300'
                }`}
              >
                {col.type}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
