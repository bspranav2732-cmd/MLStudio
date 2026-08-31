'use client';

import React, { useState, useEffect } from 'react';
import { StAlert, StMultiselect } from './StreamlitComponents';
import { api } from '../lib/api';
import { formatMetric } from '../lib/utils';
import { ProjectState } from './Sidebar';

interface CompareModelsProps {
  activeProblemType: string;
  project: ProjectState;
  setProject: React.Dispatch<React.SetStateAction<ProjectState>>;
}

export const CompareModels: React.FC<CompareModelsProps> = ({
  activeProblemType,
  project,
  setProject,
}) => {
  const [runs, setRuns] = useState<any[]>([]);
  const [selectedToRemove, setSelectedToRemove] = useState<string[]>([]);
  const [msg, setMsg] = useState<{ type: 'success' | 'warning'; text: string } | null>(null);

  const fetchComparison = async () => {
    try {
      const data = await api.getComparison();
      const allRuns = data.runs || [];
      const filtered = allRuns.filter((r: any) => r.problem_type === activeProblemType);
      setRuns(filtered);
      setProject((prev) => ({ ...prev, comparison_runs_count: allRuns.length }));
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, [activeProblemType]);

  const handleClear = async () => {
    try {
      await api.clearComparison();
      setRuns([]);
      setSelectedToRemove([]);
      setProject((prev) => ({ ...prev, comparison_runs_count: 0 }));
      setMsg({ type: 'success', text: 'Comparison cleared successfully!' });
    } catch (e) {
      console.error(e);
    }
  };

  if (runs.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="st-subheader">Compare Models</h3>
        <StAlert type="info">
          No models added yet.
          {'\n\n'}
          Train a model and click the <strong>Add Current Run to Comparison</strong> button.
        </StAlert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="st-subheader">Compare Models</h3>
        <p className="text-xs text-[var(--text-primary)]">
          Showing comparison for <strong>{activeProblemType}</strong> experiments.
        </p>
      </div>

      {/* 1. Generalization Comparison */}
      <div>
        <h4 className="text-sm font-bold text-[var(--text-primary)] mb-1">1. Generalization Comparison</h4>
        <p className="text-xs text-[var(--text-muted)] mb-2.5">
          Analyzes the performance gap between training data and validation/test data.
        </p>

        <div className="st-table-container">
          <table className="st-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>{activeProblemType === 'Regression' ? 'Training R²' : 'Training Accuracy'}</th>
                <th>{activeProblemType === 'Regression' ? 'Validation R²' : 'Validation Accuracy'}</th>
                <th>Gap</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run, i) => {
                const trainScore = activeProblemType === 'Regression'
                  ? (run.training_r2 ?? run.train_metrics?.['R2 Score'] ?? null)
                  : (run.training_accuracy ?? run.train_metrics?.['Accuracy'] ?? null);
                const valScore = activeProblemType === 'Regression'
                  ? (run.validation_r2 ?? run.validation_metrics?.['R2 Score'] ?? run.metrics?.['R2 Score'] ?? null)
                  : (run.validation_accuracy ?? run.validation_metrics?.['Accuracy'] ?? run.metrics?.['Accuracy'] ?? null);

                const trainNum = trainScore !== null && trainScore !== undefined
                  ? (typeof trainScore === 'object' ? Number(trainScore.mean) : Number(trainScore))
                  : null;
                const valNum = valScore !== null && valScore !== undefined
                  ? (typeof valScore === 'object' ? Number(valScore.mean) : Number(valScore))
                  : null;
                const gap = (trainNum !== null && valNum !== null && !isNaN(trainNum) && !isNaN(valNum))
                  ? Math.abs(trainNum - valNum)
                  : null;

                return (
                  <tr key={i}>
                    <td className="font-semibold flex items-center space-x-1.5">
                      <span>{run.model_name}</span>
                      {run.execution_mode === 'hpc' && (
                        <span className="text-[10px] px-1.5 py-0.2 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded font-mono">
                          HPC
                        </span>
                      )}
                    </td>
                    <td className="font-mono">{formatMetric(trainScore, activeProblemType !== 'Regression')}</td>
                    <td className="font-mono">{formatMetric(valScore, activeProblemType !== 'Regression')}</td>
                    <td className="font-mono font-semibold" style={{ color: 'var(--accent)' }}>
                      {gap !== null
                        ? (activeProblemType === 'Regression' ? gap.toFixed(4) : `${(gap * 100).toFixed(2)}%`)
                        : 'N/A'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Performance Comparison */}
      <div>
        <h4 className="text-sm font-bold text-[var(--text-primary)] mb-1">2. Performance Comparison</h4>
        <p className="text-xs text-[var(--text-muted)] mb-2.5">
          Compares overall performance metrics and execution time across all saved runs.
        </p>

        <div className="st-table-container overflow-x-auto">
          <table className="st-table">
            <thead>
              <tr>
                <th>Model</th>
                {activeProblemType === 'Regression' ? (
                  <>
                    <th>R²</th>
                    <th>RMSE</th>
                    <th>MAE</th>
                    <th>MAPE</th>
                  </>
                ) : (
                  <>
                    <th>Accuracy</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1 Score</th>
                  </>
                )}
                <th>Hyperparameters</th>
                <th>Training Time</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run, i) => {
                const hp = run.hyperparameters;
                const hpStr = hp && Object.keys(hp).length > 0
                  ? Object.entries(hp).map(([k, v]) => `${k}=${v}`).join(', ')
                  : 'Default';

                return (
                  <tr key={i}>
                    <td className="font-semibold">{run.model_name}</td>
                    {activeProblemType === 'Regression' ? (
                      <>
                        <td className="font-mono">{formatMetric(run.metrics?.['R2 Score'])}</td>
                        <td className="font-mono">{formatMetric(run.metrics?.['RMSE'])}</td>
                        <td className="font-mono">{formatMetric(run.metrics?.['MAE'])}</td>
                        <td className="font-mono">{formatMetric(run.metrics?.['MAPE'], true)}</td>
                      </>
                    ) : (
                      <>
                        <td className="font-mono">{formatMetric(run.metrics?.['Accuracy'], true)}</td>
                        <td className="font-mono">{formatMetric(run.metrics?.['Precision'], true)}</td>
                        <td className="font-mono">{formatMetric(run.metrics?.['Recall'], true)}</td>
                        <td className="font-mono">{formatMetric(run.metrics?.['F1 Score'], true)}</td>
                      </>
                    )}
                    <td className="text-xs max-w-xs truncate">{hpStr}</td>
                    <td className="font-mono">{Number(run.training_time || 0).toFixed(3)}s</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Manage Saved Runs */}
      <div>
        <h4 className="text-sm font-bold text-[var(--text-primary)] mb-2">3. Manage Saved Runs</h4>

        {msg && <StAlert type={msg.type}>{msg.text}</StAlert>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
          <div>
            <StMultiselect
              label="Select runs to remove:"
              options={runs.map((r, idx) => `${r.model_name} (${idx + 1})`)}
              selected={selectedToRemove}
              onChange={(val) => setSelectedToRemove(val)}
            />
            <button
              type="button"
              onClick={handleClear}
              className="st-button-secondary w-full py-1.5 mt-2 text-xs"
            >
              Clear Comparison
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
