'use client';

import React from 'react';

export interface ProjectState {
  name: string;
  dataset: string;
  rows: string | number;
  columns: string | number;
  problem: string;
  target: string;
  features_count: number;
  model: string;
  split: string;
  train_percent?: number | string;
  folds?: number | string;
  hyperparameters?: string;
  missing_strategy?: string;
  encoding_strategy?: string;
  scaling_strategy?: string;
  has_results: boolean;
  comparison_runs_count: number;
}

interface SidebarProps {
  project: ProjectState;
  appearance: 'Light' | 'Dark' | 'Follow System';
  setAppearance: (mode: 'Light' | 'Dark' | 'Follow System') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ project, appearance, setAppearance }) => {
  return (
    <aside
      className="w-72 shrink-0 border-r min-h-screen p-5 text-sm select-none"
      style={{
        backgroundColor: 'var(--sidebar-bg)',
        borderColor: 'var(--border)',
        color: 'var(--text-primary)',
      }}
    >
      {/* 1. Appearance Selectbox */}
      <div className="mb-4">
        <label className="block text-xs text-[var(--text-muted)] mb-1">Appearance</label>
        <select
          value={appearance}
          onChange={(e) => setAppearance(e.target.value as any)}
          className="st-select text-xs py-1.5"
        >
          <option value="Follow System">Follow System</option>
          <option value="Light">Light</option>
          <option value="Dark">Dark</option>
        </select>
      </div>

      {/* 2. Solvosys Title with Logo */}
      <div className="flex items-center space-x-3 mb-1">
        <img src="/solvosys.svg" alt="Solvosys Logo" className="h-8 w-8 object-contain" />
        <div>
          <h2 className="text-xl font-bold leading-tight" style={{ color: 'var(--text-primary)', margin: 0 }}>
            Solvosys
          </h2>
          <p className="text-xs italic" style={{ color: 'var(--text-muted)', margin: 0 }}>
            Machine Learning Workbench
          </p>
        </div>
      </div>

      <div className="st-divider my-3.5" />

      {/* 3. DATA Section */}
      <div className="space-y-1 text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1.5">DATA</p>
        <p className="text-[var(--text-muted)]">
          Upload Dataset: <span className="text-[var(--text-primary)]">{project.dataset || '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Rows: <span className="text-[var(--text-primary)]">{project.rows ?? '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Columns: <span className="text-[var(--text-primary)]">{project.columns ?? '-'}</span>
        </p>
      </div>

      <div className="st-divider my-3.5" />

      {/* 4. CONFIGURATION Section */}
      <div className="space-y-1 text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1.5">CONFIGURATION</p>
        <p className="text-[var(--text-muted)]">
          Problem Type: <span className="text-[var(--text-primary)]">{project.problem || '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Target Variable: <span className="text-[var(--text-primary)]">{project.target || '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Feature Selection: <span className="text-[var(--text-primary)]">{project.features_count} selected</span>
        </p>
      </div>

      <div className="st-divider my-3.5" />

      {/* 5. MODEL Section */}
      <div className="space-y-1 text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1.5">MODEL</p>
        <p className="text-[var(--text-muted)]">
          Model Selection: <span className="text-[var(--text-primary)]">{project.model || '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Hyperparameters: <span className="text-[var(--text-primary)]">{project.hyperparameters || 'Default'}</span>
        </p>
      </div>

      <div className="st-divider my-3.5" />

      {/* 6. PREPROCESSING Section */}
      <div className="space-y-1 text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1.5">PREPROCESSING</p>
        <p className="text-[var(--text-muted)]">
          Missing Values: <span className="text-[var(--text-primary)]">{project.missing_strategy || '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Encoding: <span className="text-[var(--text-primary)]">{project.encoding_strategy || '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Scaling: <span className="text-[var(--text-primary)]">{project.scaling_strategy || '-'}</span>
        </p>
      </div>

      <div className="st-divider my-3.5" />

      {/* 7. VALIDATION Section */}
      <div className="space-y-1 text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1.5">VALIDATION</p>
        <p className="text-[var(--text-muted)]">
          Split Method: <span className="text-[var(--text-primary)]">{project.split || '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Train/Test Percentage: <span className="text-[var(--text-primary)]">{project.train_percent ? `${project.train_percent}%` : '-'}</span>
        </p>
        <p className="text-[var(--text-muted)]">
          Cross Validation Folds: <span className="text-[var(--text-primary)]">{project.folds ?? '-'}</span>
        </p>
      </div>

      <div className="st-divider my-3.5" />

      {/* 8. VISUALIZATION Section */}
      <div className="space-y-1 text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1.5">VISUALIZATION</p>
        <p className="text-[var(--text-muted)]">
          Plot Settings: <span className="text-[var(--text-primary)]">{project.has_results ? 'Active' : 'Not Generated'}</span>
        </p>
      </div>

      <div className="st-divider my-3.5" />

      {/* 9. COMPARE Section */}
      <div className="space-y-1 text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1.5">COMPARE</p>
        <p className="text-[var(--text-muted)]">
          Compare Models: <span className="text-[var(--text-primary)]">{project.comparison_runs_count} runs saved</span>
        </p>
      </div>

      <div className="st-divider my-3.5" />

      {/* 10. EXPORT Section */}
      <div className="space-y-1 text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1.5">EXPORT</p>
        <p className="text-[var(--text-muted)]">
          Export Options: <span className="text-[var(--text-primary)]">{project.has_results ? 'Ready' : 'Pending'}</span>
        </p>
      </div>
    </aside>
  );
};
