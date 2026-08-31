const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface ColumnMeta {
  name: string;
  type: string;
  is_numeric: boolean;
  missing: number;
  unique: number;
  min?: number;
  max?: number;
  mean?: number;
}

export interface DatasetInfo {
  dataset_id: string;
  filename: string;
  rows: number;
  columns_count: number;
  missing_cells: number;
  columns: ColumnMeta[];
  preview: Record<string, any>[];
}

export interface Metadata {
  regression_models: string[];
  classification_models: string[];
  split_methods: string[];
  optimization_strategies: string[];
  preprocessing: {
    missing_strategies: string[];
    encoding_strategies: string[];
    scaling_strategies: string[];
  };
  regression_plots: string[];
  classification_plots: string[];
}

export interface TrainRequest {
  dataset_id: string;
  target: string;
  target_name?: string;
  target_unit?: string;
  features: string[];
  problem_type: string;
  model_name: string;
  hyperparameters?: Record<string, any>;
  split_method: string;
  train_percent: number;
  folds: number;
  repeats: number;
  optimization: string;
  opt_iters: number;
  opt_cv: number;
  use_multiple_seeds: boolean;
  num_seeds: number;
  use_oob: boolean;
  execution_mode?: 'local' | 'hpc';
  partition?: string;
  preprocessing?: {
    missing_strategy: string;
    encoding_strategy: string;
    scaling_strategy: string;
  };
}

export interface StageItem {
  stage: string;
  label: string;
  message: string;
  timestamp: number;
}

export interface OptimizationInfo {
  strategy?: string;
  iterations?: number;
  folds?: number;
  total_fits?: number;
  rows?: number;
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  current_stage?: string;
  progress: string;
  started_at?: string;
  elapsed_seconds: number;
  stages_history?: StageItem[];
  optimization_info?: OptimizationInfo;
  best_params?: Record<string, any>;
  best_cv_score?: number;
  slurm_job_id?: string | number | null;
  slurm_state?: string | null;
  compute_node?: string | null;
  partition?: string | null;
  error?: string;
}

export interface ExperimentResults {
  status: string;
  job_id: string;
  training_time: number;
  total_elapsed: number;
  problem_type: string;
  model_name: string;
  evaluation_config: Record<string, any>;
  best_params?: Record<string, any>;
  best_cv_score?: number;
  oob_score?: number | null;
  metrics: Record<string, any>;
  train_metrics?: Record<string, any>;
  training_r2?: number | null;
  validation_r2?: number | null;
  feature_importances: { feature: string; importance: number }[];
  predictions_preview: Record<string, any>[];
  available_plots: string[];
}

export interface HpcStatus {
  connected: boolean;
  mode: 'disconnected' | 'mock' | 'ssh';
  host?: string | null;
  username?: string | null;
  node?: string | null;
  auth_type?: string | null;
  message: string;
}

export interface HpcConnectRequest {
  mode: 'mock' | 'ssh';
  host?: string;
  username?: string;
  port?: number;
  key_filename?: string;
  passphrase?: string;
}

export interface HpcTransferTestResult {
  success: boolean;
  steps: {
    upload: string;
    remote_verify: string;
    download: string;
    content_verify: string;
    cleanup: string;
  };
  remote_test_dir?: string;
  message: string;
}

export interface HpcSlurmTestResult {
  success: boolean;
  job_id: string;
  partition: string;
  status: string;
  remote_test_dir?: string;
  output?: string;
  steps: {
    upload: string;
    submit: string;
    monitor: string;
    output_verify: string;
    cleanup: string;
  };
  message: string;
}

export interface HpcEnvironmentResult {
  hostname: string;
  python: string;
  python_version: string;
  numpy: string;
  pandas: string;
  scikit_learn: string;
  xgboost: string;
  catboost: string;
}

export const api = {
  async getHpcStatus(): Promise<HpcStatus> {
    const res = await fetch(`${API_BASE}/api/hpc/status`);
    if (!res.ok) throw new Error('Failed to fetch HPC status');
    return res.json();
  },

  async connectHpc(req: HpcConnectRequest): Promise<any> {
    const res = await fetch(`${API_BASE}/api/hpc/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'HPC connection failed' }));
      throw new Error(err.detail || 'HPC connection failed');
    }
    return res.json();
  },

  async disconnectHpc(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/hpc/disconnect`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to disconnect HPC');
    return res.json();
  },

  async testHpcFileTransfer(): Promise<HpcTransferTestResult> {
    const res = await fetch(`${API_BASE}/api/hpc/test-file-transfer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'File transfer test failed' }));
      throw new Error(err.detail || 'File transfer test failed');
    }
    return res.json();
  },

  async testHpcSlurmJob(partition: string): Promise<HpcSlurmTestResult> {
    const res = await fetch(`${API_BASE}/api/hpc/test-slurm-job`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ partition }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'SLURM test job failed' }));
      throw new Error(err.detail || 'SLURM test job failed');
    }
    return res.json();
  },

  async verifyHpcEnvironment(partition: string): Promise<HpcEnvironmentResult> {
    const res = await fetch(`${API_BASE}/api/hpc/verify-environment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ partition }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Environment verification failed' }));
      throw new Error(err.detail || 'Environment verification failed');
    }
    return res.json();
  },

  async testPhase53HpcRfr(partition: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/hpc/test-phase53-rfr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ partition }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Phase 5.3 test failed' }));
      throw new Error(err.detail || 'Phase 5.3 test failed');
    }
    return res.json();
  },

  async preparePhase53Test(partition: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/hpc/prepare-phase53-test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ partition }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Prepare HPC test failed' }));
      throw new Error(err.detail || 'Prepare HPC test failed');
    }
    return res.json();
  },

  async getMeta(): Promise<Metadata> {
    const res = await fetch(`${API_BASE}/api/meta`);
    if (!res.ok) throw new Error('Failed to fetch metadata');
    return res.json();
  },

  async uploadDataset(file: File): Promise<DatasetInfo> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/api/dataset/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async trainExperiment(req: TrainRequest): Promise<{ job_id: string; status: string; message: string }> {
    const res = await fetch(`${API_BASE}/api/experiments/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Training submission failed' }));
      throw new Error(err.detail || 'Training submission failed');
    }
    return res.json();
  },

  async cancelExperiment(jobId: string): Promise<{ message: string; status: string; elapsed_seconds: number }> {
    const res = await fetch(`${API_BASE}/api/experiments/${jobId}/cancel`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Cancellation failed' }));
      throw new Error(err.detail || 'Cancellation failed');
    }
    return res.json();
  },

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const res = await fetch(`${API_BASE}/api/experiments/${jobId}/status`);
    if (!res.ok) throw new Error('Failed to fetch job status');
    return res.json();
  },

  async getJobResults(jobId: string): Promise<ExperimentResults> {
    const res = await fetch(`${API_BASE}/api/experiments/${jobId}/results`);
    if (!res.ok) throw new Error('Failed to fetch job results');
    return res.json();
  },

  getPlotUrl(jobId: string, plotName: string, quality: string = 'Publication (300 DPI)', format: string = 'png'): string {
    return `${API_BASE}/api/experiments/${jobId}/plots/${encodeURIComponent(plotName)}?quality=${encodeURIComponent(quality)}&format=${format}`;
  },

  getExportScriptUrl(jobId: string): string {
    return `${API_BASE}/api/experiments/${jobId}/export/script`;
  },

  getExportCsvUrl(jobId: string): string {
    return `${API_BASE}/api/experiments/${jobId}/export/csv`;
  },

  getExportPdfUrl(jobId: string): string {
    return `${API_BASE}/api/experiments/${jobId}/export/pdf`;
  },

  getExportZipUrl(jobId: string): string {
    return `${API_BASE}/api/experiments/${jobId}/export/zip`;
  },

  async addToComparison(jobId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/comparison/add/${jobId}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to add to comparison');
    return res.json();
  },

  async getComparison(): Promise<{ runs: any[] }> {
    const res = await fetch(`${API_BASE}/api/comparison`);
    if (!res.ok) throw new Error('Failed to fetch comparison');
    return res.json();
  },

  async clearComparison(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/comparison/clear`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to clear comparison');
    return res.json();
  },
};
