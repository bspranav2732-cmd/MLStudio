'use client';

import React, { useState, useEffect } from 'react';
import { Download, FileCode, FileSpreadsheet, FileText, Archive, Check, Copy } from 'lucide-react';
import { ExperimentResults, api } from '../lib/api';

interface ExportPanelProps {
  results: ExperimentResults;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({ results }) => {
  const [activeTab, setActiveTab] = useState<'script' | 'csv' | 'pdf' | 'zip'>('script');
  const [scriptCode, setScriptCode] = useState<string>('');
  const [loadingScript, setLoadingScript] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    const fetchScript = async () => {
      setLoadingScript(true);
      try {
        const res = await fetch(api.getExportScriptUrl(results.job_id));
        if (res.ok) {
          const text = await res.text();
          setScriptCode(text);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingScript(false);
      }
    };
    fetchScript();
  }, [results.job_id]);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(scriptCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
      <div className="pb-4 border-b border-slate-800">
        <h2 className="text-base font-semibold text-white">📤 Export & Experiment Replication</h2>
        <p className="text-xs text-slate-400">Export standalone reproducibility artifacts for academic publications or peer review</p>
      </div>

      {/* Tabs */}
      <div className="mt-4 flex space-x-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab('script')}
          className={`flex items-center space-x-1.5 rounded-lg px-3.5 py-2 text-xs font-medium transition-all ${
            activeTab === 'script' ? 'bg-blue-600 text-white' : 'bg-slate-800/60 text-slate-400 hover:text-white'
          }`}
        >
          <FileCode className="h-4 w-4" />
          <span>Standalone Python Script</span>
        </button>

        <button
          onClick={() => setActiveTab('csv')}
          className={`flex items-center space-x-1.5 rounded-lg px-3.5 py-2 text-xs font-medium transition-all ${
            activeTab === 'csv' ? 'bg-blue-600 text-white' : 'bg-slate-800/60 text-slate-400 hover:text-white'
          }`}
        >
          <FileSpreadsheet className="h-4 w-4" />
          <span>Predictions CSV</span>
        </button>

        <button
          onClick={() => setActiveTab('pdf')}
          className={`flex items-center space-x-1.5 rounded-lg px-3.5 py-2 text-xs font-medium transition-all ${
            activeTab === 'pdf' ? 'bg-blue-600 text-white' : 'bg-slate-800/60 text-slate-400 hover:text-white'
          }`}
        >
          <FileText className="h-4 w-4" />
          <span>Academic PDF Report</span>
        </button>

        <button
          onClick={() => setActiveTab('zip')}
          className={`flex items-center space-x-1.5 rounded-lg px-3.5 py-2 text-xs font-medium transition-all ${
            activeTab === 'zip' ? 'bg-blue-600 text-white' : 'bg-slate-800/60 text-slate-400 hover:text-white'
          }`}
        >
          <Archive className="h-4 w-4" />
          <span>Full Experiment ZIP Bundle</span>
        </button>
      </div>

      {/* Tab Contents */}
      <div className="mt-5">
        {activeTab === 'script' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-300">
                Self-contained Python script including exact dataset partitioning, preprocessing transformers, hyperparameter optimization (if enabled), model fitting, and figure generation with zero external framework dependencies.
              </p>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={handleCopyCode}
                  className="flex items-center space-x-1 rounded-lg bg-slate-800 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700 border border-slate-700"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copied ? 'Copied!' : 'Copy Code'}</span>
                </button>
                <a
                  href={api.getExportScriptUrl(results.job_id)}
                  download={`run_${results.model_name.toLowerCase().replace(/ /g, '_')}.py`}
                  className="flex items-center space-x-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-500"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Download (.py)</span>
                </a>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre">{loadingScript ? 'Loading generated Python script...' : scriptCode}</pre>
            </div>
          </div>
        )}

        {activeTab === 'csv' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-300">
                Download a clean tabular CSV containing the true test targets, model predictions, and calculated residuals or class probabilities.
              </p>
              <a
                href={api.getExportCsvUrl(results.job_id)}
                download={`predictions_${results.model_name.toLowerCase().replace(/ /g, '_')}.csv`}
                className="flex items-center space-x-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download Predictions (.csv)</span>
              </a>
            </div>
          </div>
        )}

        {activeTab === 'pdf' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-300">
                Download a publication-grade ReportLab PDF summarizing dataset attributes, preprocessor configurations, hyperparameter search results, evaluation metrics, and embedded publication plots with numbered headers and footers.
              </p>
              <a
                href={api.getExportPdfUrl(results.job_id)}
                download={`report_${results.model_name.toLowerCase().replace(/ /g, '_')}.pdf`}
                className="flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download PDF Research Report</span>
              </a>
            </div>
          </div>
        )}

        {activeTab === 'zip' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-300">
                Complete reproducibility archive containing the standalone Python script, dataset CSV, prediction CSV, PDF research report, generated publication figures, README.md, and requirements.txt.
              </p>
              <a
                href={api.getExportZipUrl(results.job_id)}
                download={`experiment_bundle_${results.model_name.toLowerCase().replace(/ /g, '_')}.zip`}
                className="flex items-center space-x-1.5 rounded-lg bg-purple-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-purple-500"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download Full Bundle (.zip)</span>
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
