'use client';

import React, { useState } from 'react';
import { Image as ImageIcon, Download, Settings, RefreshCw } from 'lucide-react';
import { ExperimentResults, api } from '../lib/api';

interface PlotViewerProps {
  results: ExperimentResults;
}

export const PlotViewer: React.FC<PlotViewerProps> = ({ results }) => {
  const plots = results.available_plots || [];
  const [selectedPlot, setSelectedPlot] = useState<string>(plots[0] || 'Actual vs Predicted');
  const [quality, setQuality] = useState<string>('Publication (300 DPI)');
  const [format, setFormat] = useState<string>('png');
  const [key, setKey] = useState<number>(0);

  const plotUrl = api.getPlotUrl(results.job_id, selectedPlot, quality, format);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400">
            <ImageIcon className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Publication Visualizations</h2>
            <p className="text-xs text-slate-400">Generate, inspect, and export publication-quality scientific figures</p>
          </div>
        </div>

        {/* Quality Controls */}
        <div className="flex items-center space-x-3 text-xs">
          <div>
            <select
              value={quality}
              onChange={(e) => {
                setQuality(e.target.value);
                setKey((k) => k + 1);
              }}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
            >
              <option value="Screen Preview (150 DPI)">150 DPI (Preview)</option>
              <option value="Publication (300 DPI)">300 DPI (Publication Standard)</option>
              <option value="High Quality (600 DPI)">600 DPI (High Resolution)</option>
              <option value="Ultra Quality (1200 DPI)">1200 DPI (Ultra)</option>
            </select>
          </div>

          <a
            href={plotUrl}
            download={`${selectedPlot.toLowerCase().replace(/ /g, '_')}.${format}`}
            className="flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download Image</span>
          </a>
        </div>
      </div>

      {/* Plot Tabs */}
      <div className="mt-4 flex flex-wrap gap-1.5 border-b border-slate-800/80 pb-3">
        {plots.map((p) => (
          <button
            key={p}
            onClick={() => {
              setSelectedPlot(p);
              setKey((k) => k + 1);
            }}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
              selectedPlot === p
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Plot Image Display */}
      <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-slate-800 bg-slate-950/80 p-6 min-h-[420px]">
        <img
          key={`${selectedPlot}-${key}-${quality}`}
          src={plotUrl}
          alt={selectedPlot}
          className="max-h-[500px] w-auto rounded-lg shadow-lg object-contain"
          loading="lazy"
        />
        <p className="mt-4 text-xs font-medium text-slate-400">
          Figure: <strong className="text-slate-200">{selectedPlot}</strong> • Styled with serif typography & academic grid
        </p>
      </div>
    </div>
  );
};
