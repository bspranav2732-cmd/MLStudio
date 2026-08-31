'use client';

import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, AlertCircle, CheckCircle2, Table, Database } from 'lucide-react';
import { DatasetInfo, api } from '../lib/api';

interface DatasetUploadProps {
  onDatasetLoaded: (info: DatasetInfo) => void;
  currentDataset: DatasetInfo | null;
}

export const DatasetUpload: React.FC<DatasetUploadProps> = ({ onDatasetLoaded, currentDataset }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a valid CSV file.');
      return;
    }
    setError(null);
    setIsUploading(true);
    try {
      const info = await api.uploadDataset(file);
      onDatasetLoaded(info);
    } catch (err: any) {
      setError(err.message || 'Failed to upload dataset');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-sm">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
            <Database className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">1. Dataset Selection & Ingestion</h2>
            <p className="text-xs text-slate-400">Upload your CSV tabular dataset to begin experiment modeling</p>
          </div>
        </div>

        {currentDataset && (
          <div className="flex items-center space-x-2 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20">
            <CheckCircle2 className="h-4 w-4" />
            <span className="font-medium">Loaded: {currentDataset.filename}</span>
          </div>
        )}
      </div>

      {/* Upload Box */}
      <div className="mt-5">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`group flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all duration-200 ${
            dragOver
              ? 'border-blue-500 bg-blue-500/10'
              : 'border-slate-700 bg-slate-800/40 hover:border-slate-600 hover:bg-slate-800/70'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFile(e.target.files[0]);
              }
            }}
          />

          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-800 text-blue-400 group-hover:bg-blue-600 group-hover:text-white transition-all">
            <UploadCloud className="h-6 w-6" />
          </div>

          <p className="mt-3 text-sm font-medium text-slate-200">
            {isUploading ? 'Uploading and parsing dataset...' : 'Click or drag & drop CSV dataset here'}
          </p>
          <p className="mt-1 text-xs text-slate-400">Supports standard CSV formats with header row</p>
        </div>

        {error && (
          <div className="mt-4 flex items-center space-x-2 rounded-lg bg-rose-500/10 p-3.5 text-xs text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Dataset Summary & Table Preview */}
        {currentDataset && (
          <div className="mt-6 space-y-4">
            {/* Quick Stat Badges */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-xl bg-slate-800/60 p-3.5 border border-slate-700/60">
                <span className="text-xs text-slate-400">Total Rows</span>
                <p className="text-lg font-bold text-white">{currentDataset.rows.toLocaleString()}</p>
              </div>
              <div className="rounded-xl bg-slate-800/60 p-3.5 border border-slate-700/60">
                <span className="text-xs text-slate-400">Total Columns</span>
                <p className="text-lg font-bold text-white">{currentDataset.columns_count}</p>
              </div>
              <div className="rounded-xl bg-slate-800/60 p-3.5 border border-slate-700/60">
                <span className="text-xs text-slate-400">Numeric Features</span>
                <p className="text-lg font-bold text-blue-400">
                  {currentDataset.columns.filter((c) => c.is_numeric).length}
                </p>
              </div>
              <div className="rounded-xl bg-slate-800/60 p-3.5 border border-slate-700/60">
                <span className="text-xs text-slate-400">Missing Values</span>
                <p className={`text-lg font-bold ${currentDataset.missing_cells > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {currentDataset.missing_cells}
                </p>
              </div>
            </div>

            {/* Preview Table */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800 text-xs font-medium text-slate-300">
                <div className="flex items-center space-x-2">
                  <Table className="h-4 w-4 text-slate-400" />
                  <span>Dataset Preview (Top 10 Rows)</span>
                </div>
                <span className="text-slate-500">Previewing first {currentDataset.preview.length} rows</span>
              </div>
              <div className="overflow-x-auto max-h-56">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="sticky top-0 bg-slate-900/95 text-slate-400 border-b border-slate-800 font-semibold">
                    <tr>
                      {currentDataset.columns.map((col) => (
                        <th key={col.name} className="px-3 py-2 whitespace-nowrap">
                          <div className="flex items-center space-x-1.5">
                            <span>{col.name}</span>
                            <span className={`text-[10px] px-1.5 py-0.2 rounded ${col.is_numeric ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'}`}>
                              {col.type}
                            </span>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {currentDataset.preview.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        {currentDataset.columns.map((col) => (
                          <td key={col.name} className="px-3 py-1.5 whitespace-nowrap font-mono text-[11px] text-slate-300">
                            {row[col.name] !== null && row[col.name] !== undefined ? String(row[col.name]) : <span className="text-slate-500 italic">null</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
