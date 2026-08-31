'use client';

import React, { useState } from 'react';
import { Cpu, Split, Zap, Sliders, ChevronDown, ChevronUp, Sparkles, RefreshCw } from 'lucide-react';
import { Metadata } from '../lib/api';

interface ModelConfigPanelProps {
  meta: Metadata | null;
  problemType: 'Regression' | 'Classification';
  modelName: string;
  setModelName: (m: string) => void;
  splitMethod: string;
  setSplitMethod: (s: string) => void;
  trainPercent: number;
  setTrainPercent: (p: number) => void;
  folds: number;
  setFolds: (f: number) => void;
  repeats: number;
  setRepeats: (r: number) => void;
  optimization: string;
  setOptimization: (o: string) => void;
  optIters: number;
  setOptIters: (i: number) => void;
  optCv: number;
  setOptCv: (c: number) => void;
  useMultipleSeeds: boolean;
  setUseMultipleSeeds: (b: boolean) => void;
  numSeeds: number;
  setNumSeeds: (n: number) => void;
  useOob: boolean;
  setUseOob: (b: boolean) => void;
}

export const ModelConfigPanel: React.FC<ModelConfigPanelProps> = ({
  meta,
  problemType,
  modelName,
  setModelName,
  splitMethod,
  setSplitMethod,
  trainPercent,
  setTrainPercent,
  folds,
  setFolds,
  repeats,
  setRepeats,
  optimization,
  setOptimization,
  optIters,
  setOptIters,
  optCv,
  setOptCv,
  useMultipleSeeds,
  setUseMultipleSeeds,
  numSeeds,
  setNumSeeds,
  useOob,
  setUseOob,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const availableModels = meta
    ? problemType === 'Regression'
      ? meta.regression_models
      : meta.classification_models
    : [];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
      <div className="flex items-center space-x-2.5 pb-4 border-b border-slate-800">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
          <Cpu className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-white">5. Model Architecture & Validation Strategy</h2>
          <p className="text-xs text-slate-400">Select learner algorithm, evaluation partitioning, and hyperparameter tuning</p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Model Selection */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <label className="block text-xs font-semibold text-slate-200 mb-1.5">Machine Learning Model</label>
          <select
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm text-white font-medium focus:border-blue-500 focus:outline-none"
          >
            {availableModels.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <p className="mt-2 text-[11px] text-slate-400">
            {modelName === 'Random Forest' && 'Ensemble of decision trees with bagging and feature subsampling.'}
            {modelName === 'XGBoost Regressor' && 'Gradient boosted decision trees with regularized objective functions.'}
            {modelName === 'CatBoost Regressor' && 'Gradient boosting with native categorical handling and symmetric trees.'}
            {modelName === 'Linear Regression' && 'Standard Ordinary Least Squares linear regression.'}
            {modelName === 'Polynomial Regression' && 'Linear regression with non-linear polynomial feature expansions.'}
            {modelName === 'Lasso Regression' && 'Linear model with L1 regularization for sparsity and feature selection.'}
            {modelName === 'Elastic Net' && 'Linear model combining L1 and L2 penalty terms.'}
            {modelName === 'Decision Tree' && 'Single interpretable decision tree partitioning feature space.'}
            {modelName === 'Logistic Regression' && 'Log-odds linear classifier with L2/L1 regularization.'}
          </p>
        </div>

        {/* Validation Strategy */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <label className="block text-xs font-semibold text-slate-200 mb-1.5">Validation Strategy</label>
          <select
            value={splitMethod}
            onChange={(e) => setSplitMethod(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="Train-Test Split">Train-Test Split</option>
            <option value="K-Fold Cross Validation">K-Fold Cross Validation</option>
            <option value="Stratified K-Fold Cross Validation">Stratified K-Fold CV</option>
            <option value="Repeated K-Fold">Repeated K-Fold CV</option>
            <option value="Repeated Stratified K-Fold">Repeated Stratified K-Fold CV</option>
          </select>

          {/* Conditional Validation Controls */}
          {splitMethod === 'Train-Test Split' && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Train / Test Ratio:</span>
                <span className="font-mono text-blue-400">{trainPercent}% / {100 - trainPercent}%</span>
              </div>
              <input
                type="range"
                min={50}
                max={95}
                step={5}
                value={trainPercent}
                onChange={(e) => setTrainPercent(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          )}

          {splitMethod.includes('K-Fold') && (
            <div className="mt-3 space-y-2">
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Number of Folds (K):</span>
                  <span className="font-mono text-blue-400">{folds} folds</span>
                </div>
                <input
                  type="range"
                  min={2}
                  max={20}
                  step={1}
                  value={folds}
                  onChange={(e) => setFolds(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {splitMethod.includes('Repeated') && (
                <div>
                  <div className="flex justify-between text-xs text-slate-300 mb-1">
                    <span>Repeats:</span>
                    <span className="font-mono text-purple-400">{repeats} repeats</span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    step={1}
                    value={repeats}
                    onChange={(e) => setRepeats(Number(e.target.value))}
                    className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Hyperparameter Optimization */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <label className="block text-xs font-semibold text-slate-200 mb-1.5">Hyperparameter Optimization</label>
          <select
            value={optimization}
            onChange={(e) => setOptimization(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="None">None (Default Parameters)</option>
            <option value="Random Search">Random Search (RandomizedSearchCV)</option>
            <option value="Grid Search">Grid Search (GridSearchCV)</option>
          </select>

          {/* Conditional Optimization Controls */}
          {optimization === 'Random Search' && (
            <div className="mt-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-300">Iterations (Candidates):</span>
                <span className="font-mono text-xs text-amber-400">{optIters}</span>
              </div>
              <input
                type="range"
                min={5}
                max={50}
                step={5}
                value={optIters}
                onChange={(e) => setOptIters(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />

              <div className="flex items-center justify-between pt-1">
                <span className="text-xs text-slate-300">Internal CV Folds:</span>
                <span className="font-mono text-xs text-amber-400">{optCv} folds</span>
              </div>
              <input
                type="range"
                min={2}
                max={10}
                step={1}
                value={optCv}
                onChange={(e) => setOptCv(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <p className="text-[10px] text-slate-400">Total fits: {optIters} × {optCv} = {optIters * optCv} fits</p>
            </div>
          )}

          {optimization === 'Grid Search' && (
            <div className="mt-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-300">Internal CV Folds:</span>
                <span className="font-mono text-xs text-amber-400">{optCv} folds</span>
              </div>
              <input
                type="range"
                min={2}
                max={10}
                step={1}
                value={optCv}
                onChange={(e) => setOptCv(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
            </div>
          )}
        </div>
      </div>

      {/* Advanced Settings Collapsible */}
      <div className="mt-4 border-t border-slate-800/80 pt-3">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          <span>Advanced Statistical & Research Settings</span>
        </button>

        {showAdvanced && (
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 rounded-xl bg-slate-950/50 p-4 border border-slate-800">
            {/* Multiple Random Seeds */}
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                id="multi_seed"
                checked={useMultipleSeeds}
                onChange={(e) => setUseMultipleSeeds(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500"
              />
              <div className="flex-1">
                <label htmlFor="multi_seed" className="text-xs font-semibold text-slate-200 cursor-pointer">
                  Multiple Random Seed Evaluation
                </label>
                <p className="text-[11px] text-slate-400">
                  Runs the full experiment over N independent random states to compute true statistical mean ± std metrics.
                </p>
                {useMultipleSeeds && (
                  <div className="mt-2 flex items-center space-x-2">
                    <span className="text-xs text-slate-300">Seed Iterations:</span>
                    <input
                      type="number"
                      min={2}
                      max={20}
                      value={numSeeds}
                      onChange={(e) => setNumSeeds(Number(e.target.value))}
                      className="w-16 rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-white"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Random Forest OOB Score */}
            {modelName === 'Random Forest' && (
              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  id="oob_score"
                  checked={useOob}
                  onChange={(e) => setUseOob(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <label htmlFor="oob_score" className="text-xs font-semibold text-slate-200 cursor-pointer">
                    Enable Out-Of-Bag (OOB) Estimation
                  </label>
                  <p className="text-[11px] text-slate-400">
                    Calculates generalized test error during bootstrap aggregation without requiring an external validation split.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
