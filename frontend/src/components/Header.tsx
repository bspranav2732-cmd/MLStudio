'use client';

import React from 'react';
import { Activity, Sparkles, BookOpen, Layers, ShieldCheck } from 'lucide-react';

interface HeaderProps {
  activeTab: 'experiment' | 'comparison';
  setActiveTab: (tab: 'experiment' | 'comparison') => void;
  datasetName?: string;
  rows?: number;
  cols?: number;
  modelName?: string;
  isTraining?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  datasetName,
  rows,
  cols,
  modelName,
  isTraining,
}) => {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
        {/* Left: Brand / Title */}
        <div className="flex items-center space-x-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-md shadow-blue-500/20">
            <Layers className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">Solvosys</h1>
              <span className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-400 border border-blue-500/20">
                Research Edition
              </span>
            </div>
            <p className="text-xs text-slate-400">Next-Gen Machine Learning Workbench</p>
          </div>
        </div>

        {/* Center: Quick Project Status Badges */}
        <div className="hidden md:flex items-center space-x-3 text-xs">
          {datasetName && (
            <div className="flex items-center space-x-1.5 rounded-lg bg-slate-800/80 px-3 py-1.5 text-slate-300 border border-slate-700">
              <BookOpen className="h-3.5 w-3.5 text-emerald-400" />
              <span className="font-medium text-white">{datasetName}</span>
              {rows !== undefined && cols !== undefined && (
                <span className="text-slate-400">({rows} × {cols})</span>
              )}
            </div>
          )}

          {modelName && (
            <div className="flex items-center space-x-1.5 rounded-lg bg-slate-800/80 px-3 py-1.5 text-slate-300 border border-slate-700">
              <Activity className="h-3.5 w-3.5 text-blue-400" />
              <span className="text-slate-400">Model:</span>
              <span className="font-medium text-white">{modelName}</span>
            </div>
          )}

          {isTraining && (
            <div className="flex items-center space-x-1.5 rounded-lg bg-amber-500/10 px-3 py-1.5 text-amber-400 border border-amber-500/20 animate-pulse">
              <div className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
              <span className="font-semibold">Training Active</span>
            </div>
          )}
        </div>

        {/* Right: Tab Navigation */}
        <div className="flex items-center space-x-2">
          <div className="flex rounded-lg bg-slate-800 p-1 border border-slate-700/60">
            <button
              onClick={() => setActiveTab('experiment')}
              className={`flex items-center space-x-1.5 rounded-md px-3.5 py-1.5 text-xs font-medium transition-all ${
                activeTab === 'experiment'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Experiment</span>
            </button>
            <button
              onClick={() => setActiveTab('comparison')}
              className={`flex items-center space-x-1.5 rounded-md px-3.5 py-1.5 text-xs font-medium transition-all ${
                activeTab === 'comparison'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Compare Models</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
