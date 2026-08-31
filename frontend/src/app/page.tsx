'use client';

import React, { useState, useEffect } from 'react';
import { Sidebar, ProjectState } from '../components/Sidebar';
import { CurrentExperiment } from '../components/CurrentExperiment';
import { CompareModels } from '../components/CompareModels';
import { StTabs } from '../components/StreamlitComponents';
import { DatasetInfo, Metadata, api } from '../lib/api';

export default function SolvosysApp() {
  const [appearance, setAppearance] = useState<'Light' | 'Dark' | 'Follow System'>('Dark');
  const [meta, setMeta] = useState<Metadata | null>(null);
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);
  const [mainTab, setMainTab] = useState<string>('Current Experiment');

  const [project, setProject] = useState<ProjectState>({
    name: 'Untitled',
    dataset: 'No Dataset',
    rows: '-',
    columns: '-',
    problem: '-',
    target: '-',
    features_count: 0,
    model: 'Random Forest',
    split: 'Train-Test Split',
    train_percent: 80,
    folds: 5,
    hyperparameters: 'Default',
    missing_strategy: 'None',
    encoding_strategy: 'None',
    scaling_strategy: 'None',
    has_results: false,
    comparison_runs_count: 0,
  });

  // Load initial backend metadata
  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const data = await api.getMeta();
        setMeta(data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchMeta();
  }, []);

  // Sync theme with HTML class
  useEffect(() => {
    let isDark = true;
    if (appearance === 'Light') {
      isDark = false;
    } else if (appearance === 'Dark') {
      isDark = true;
    } else {
      isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [appearance]);

  return (
    <div className="flex min-h-screen" style={{ backgroundColor: 'var(--bg)', color: 'var(--text-primary)' }}>
      {/* 1. Left Streamlit Sidebar */}
      <Sidebar
        project={project}
        appearance={appearance}
        setAppearance={setAppearance}
      />

      {/* 2. Main Streamlit Content Area */}
      <main className="flex-1 p-8 max-w-5xl overflow-y-auto">
        {/* Solvosys Title */}
        <h1 className="st-title">
          <img src="/solvosys.svg" alt="Solvosys" className="h-10 w-10 object-contain" />
          <span>Solvosys</span>
        </h1>

        {/* Top Streamlit Tabs */}
        <StTabs
          tabs={['Current Experiment', 'Compare Models']}
          activeTab={mainTab}
          onChange={(tab) => setMainTab(tab)}
        />

        <div className="mt-4">
          {mainTab === 'Current Experiment' ? (
            <CurrentExperiment
              meta={meta}
              dataset={dataset}
              onDatasetLoaded={(d) => setDataset(d)}
              project={project}
              setProject={setProject}
            />
          ) : (
            <CompareModels
              activeProblemType={project.problem === 'Classification' ? 'Classification' : 'Regression'}
              project={project}
              setProject={setProject}
            />
          )}
        </div>
      </main>
    </div>
  );
}
