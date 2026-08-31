'use client';

import React from 'react';
import { Loader2, CheckCircle2, XCircle, Clock, Zap } from 'lucide-react';
import { JobStatus } from '../lib/api';

interface TrainingStatusProps {
  status: JobStatus | null;
  onCancel?: () => void;
}

export const TrainingStatus: React.FC<TrainingStatusProps> = ({ status }) => {
  if (!status) return null;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Left: Status Icon & Message */}
        <div className="flex items-center space-x-3.5">
          {status.status === 'running' && (
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          )}
          {status.status === 'queued' && (
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400">
              <Clock className="h-5 w-5 animate-pulse" />
            </div>
          )}
          {status.status === 'completed' && (
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          )}
          {status.status === 'failed' && (
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400">
              <XCircle className="h-5 w-5" />
            </div>
          )}

          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-white capitalize">
                {status.status === 'running' && 'Experiment Executing in Background'}
                {status.status === 'queued' && 'Experiment Queued'}
                {status.status === 'completed' && 'Training & Evaluation Succeeded'}
                {status.status === 'failed' && 'Experiment Failed'}
              </h3>
              <span className="text-[11px] font-mono text-slate-500">ID: {status.job_id.slice(0, 8)}</span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">{status.progress || 'Processing...'}</p>
          </div>
        </div>

        {/* Right: Elapsed Timer */}
        <div className="flex items-center space-x-3 self-end sm:self-center">
          <div className="rounded-xl bg-slate-800 px-3.5 py-1.5 border border-slate-700 text-xs font-mono text-slate-300">
            <span className="text-slate-500 mr-1.5">Elapsed:</span>
            <span className="font-bold text-blue-400">{status.elapsed_seconds.toFixed(1)}s</span>
          </div>
        </div>
      </div>

      {status.status === 'running' && (
        <div className="mt-3.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
          <div className="h-full w-full bg-gradient-to-r from-blue-600 via-indigo-500 to-blue-600 animate-[shimmer_2s_infinite]" />
        </div>
      )}

      {status.error && (
        <div className="mt-3 rounded-lg bg-rose-500/10 p-3 text-xs text-rose-300 border border-rose-500/20">
          <strong>Error:</strong> {status.error}
        </div>
      )}
    </div>
  );
};
