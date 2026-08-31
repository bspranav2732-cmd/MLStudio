'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileCode,
  FileSpreadsheet,
  FileText,
  Archive,
  Loader2,
  Download,
  Square,
  CheckCircle2,
  CircleDot,
  Circle,
  Server,
  Wifi,
  WifiOff,
  FileCheck,
  Terminal,
  FolderUp,
  Clock
} from 'lucide-react';
import {
  StMetric,
  StAlert,
  StSelect,
  StSlider,
  StRadio,
  StMultiselect,
  StExpander,
  StTabs,
} from './StreamlitComponents';
import { DatasetInfo, Metadata, JobStatus, ExperimentResults, HpcStatus, HpcTransferTestResult, HpcSlurmTestResult, HpcEnvironmentResult, api } from '../lib/api';
import { formatMetric } from '../lib/utils';
import { ProjectState } from './Sidebar';

interface CurrentExperimentProps {
  meta: Metadata | null;
  dataset: DatasetInfo | null;
  onDatasetLoaded: (info: DatasetInfo) => void;
  project: ProjectState;
  setProject: React.Dispatch<React.SetStateAction<ProjectState>>;
}

export const CurrentExperiment: React.FC<CurrentExperimentProps> = ({
  meta,
  dataset,
  onDatasetLoaded,
  project,
  setProject,
}) => {
  // Target & Problem
  const [target, setTarget] = useState<string>('');
  const [targetUnit, setTargetUnit] = useState<string>('');
  const [problemType, setProblemType] = useState<string>('Regression');

  // Features
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);

  // Model & Validation
  const [modelName, setModelName] = useState<string>('Random Forest');
  const [splitMethod, setSplitMethod] = useState<string>('Train-Test Split');
  const [trainPercent, setTrainPercent] = useState<number>(80);
  const [folds, setFolds] = useState<number>(5);
  const [repeats, setRepeats] = useState<number>(3);
  const [optimization, setOptimization] = useState<string>('None');
  const [optIters, setOptIters] = useState<number>(10);
  const [optCv, setOptCv] = useState<number>(3);
  const [useMultipleSeeds, setUseMultipleSeeds] = useState<boolean>(false);
  const [numSeeds, setNumSeeds] = useState<number>(5);
  const [useOob, setUseOob] = useState<boolean>(false);
  const [executionMode, setExecutionMode] = useState<'local' | 'hpc'>('local');

  // Preprocessing
  const [missingStrategy, setMissingStrategy] = useState<string>('None');
  const [encodingStrategy, setEncodingStrategy] = useState<string>('None');
  const [scalingStrategy, setScalingStrategy] = useState<string>('None');

  // Hyperparameters
  const [rfTrees, setRfTrees] = useState<number>(100);
  const [rfDepth, setRfDepth] = useState<number>(0);
  const [rfSplit, setRfSplit] = useState<number>(2);
  const [rfLeaf, setRfLeaf] = useState<number>(1);
  const [rfFeatures, setRfFeatures] = useState<string>('sqrt');

  // Execution & Results
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [results, setResults] = useState<ExperimentResults | null>(null);
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [trainError, setTrainError] = useState<string | null>(null);
  const [cancelledMsg, setCancelledMsg] = useState<string | null>(null);
  const [comparisonAdded, setComparisonAdded] = useState<boolean>(false);

  // Plot settings
  const [selectedPlots, setSelectedPlots] = useState<string[]>(['Actual vs Predicted', 'Residual Plot']);
  const [plotQuality, setPlotQuality] = useState<string>('Publication (300 DPI)');
  const [figureWidth, setFigureWidth] = useState<string>('Double Column (190 mm)');
  const [exportFormat, setExportFormat] = useState<string>('PNG');
  const [plotsGenerated, setPlotsGenerated] = useState<boolean>(false);

  // Export Tab
  const [exportTab, setExportTab] = useState<string>('Python Script');
  const [scriptCode, setScriptCode] = useState<string>('');

  // HPC State
  const [hpcStatus, setHpcStatus] = useState<HpcStatus>({
    connected: false,
    mode: 'disconnected',
    message: 'Not Connected',
  });
  const [hpcMode, setHpcMode] = useState<'mock' | 'ssh'>('mock');
  const [hpcHost, setHpcHost] = useState<string>('');
  const [hpcUsername, setHpcUsername] = useState<string>('');
  const [hpcPort, setHpcPort] = useState<number>(22);
  const [hpcPassphrase, setHpcPassphrase] = useState<string>('');
  const [isConnectingHpc, setIsConnectingHpc] = useState<boolean>(false);
  const [hpcError, setHpcError] = useState<string | null>(null);
  const [isTestingTransfer, setIsTestingTransfer] = useState<boolean>(false);
  const [transferTestResult, setTransferTestResult] = useState<HpcTransferTestResult | null>(null);
  const [transferTestError, setTransferTestError] = useState<string | null>(null);
  const [hpcPartition, setHpcPartition] = useState<string>('');
  const [isTestingSlurm, setIsTestingSlurm] = useState<boolean>(false);
  const [slurmTestResult, setSlurmTestResult] = useState<HpcSlurmTestResult | null>(null);
  const [slurmTestError, setSlurmTestError] = useState<string | null>(null);
  const [isVerifyingEnv, setIsVerifyingEnv] = useState<boolean>(false);
  const [envTestResult, setEnvTestResult] = useState<HpcEnvironmentResult | null>(null);
  const [envTestError, setEnvTestError] = useState<string | null>(null);
  const [isTestingPhase53, setIsTestingPhase53] = useState<boolean>(false);
  const [phase53Result, setPhase53Result] = useState<any | null>(null);
  const [phase53Error, setPhase53Error] = useState<string | null>(null);
  const [isPreparingTest, setIsPreparingTest] = useState<boolean>(false);
  const [prepareResult, setPrepareResult] = useState<any | null>(null);
  const [prepareError, setPrepareError] = useState<string | null>(null);

  const pollRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync HPC connection status
  useEffect(() => {
    if (executionMode === 'hpc') {
      api.getHpcStatus().then(setHpcStatus).catch(() => {});
    }
  }, [executionMode]);

  const handleConnectHpc = async () => {
    setIsConnectingHpc(true);
    setHpcError(null);
    setTransferTestResult(null);
    setTransferTestError(null);
    setSlurmTestResult(null);
    setSlurmTestError(null);
    try {
      await api.connectHpc({
        mode: hpcMode,
        host: hpcMode === 'ssh' && hpcHost ? hpcHost.trim() : undefined,
        username: hpcMode === 'ssh' && hpcUsername ? hpcUsername.trim() : undefined,
        port: hpcMode === 'ssh' ? Number(hpcPort) || 22 : undefined,
        passphrase: hpcMode === 'ssh' && hpcPassphrase ? hpcPassphrase : undefined,
      });
      const st = await api.getHpcStatus();
      setHpcStatus(st);
      // Immediately clear passphrase from memory after successful connection
      setHpcPassphrase('');
    } catch (err: any) {
      setHpcError(err.message || 'Connection failed');
    } finally {
      setIsConnectingHpc(false);
    }
  };

  const handleDisconnectHpc = async () => {
    try {
      await api.disconnectHpc();
      const st = await api.getHpcStatus();
      setHpcStatus(st);
      setTransferTestResult(null);
      setTransferTestError(null);
      setSlurmTestResult(null);
      setSlurmTestError(null);
      setHpcPassphrase('');
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleTestFileTransfer = async () => {
    setIsTestingTransfer(true);
    setTransferTestError(null);
    setTransferTestResult(null);
    try {
      const res = await api.testHpcFileTransfer();
      setTransferTestResult(res);
    } catch (err: any) {
      setTransferTestError(err.message || 'File transfer test failed');
    } finally {
      setIsTestingTransfer(false);
    }
  };

  const handleTestSlurmJob = async () => {
    if (!hpcPartition.trim()) {
      setSlurmTestError('Please enter a SLURM partition name.');
      return;
    }
    setIsTestingSlurm(true);
    setSlurmTestError(null);
    setSlurmTestResult(null);
    try {
      const res = await api.testHpcSlurmJob(hpcPartition.trim());
      setSlurmTestResult(res);
    } catch (err: any) {
      setSlurmTestError(err.message || 'SLURM test job failed');
    } finally {
      setIsTestingSlurm(false);
    }
  };

  const handleVerifyEnv = async () => {
    if (!hpcPartition.trim()) {
      setEnvTestError('Please enter a SLURM partition name.');
      return;
    }
    setIsVerifyingEnv(true);
    setEnvTestError(null);
    setEnvTestResult(null);
    try {
      const res = await api.verifyHpcEnvironment(hpcPartition.trim());
      setEnvTestResult(res);
    } catch (err: any) {
      setEnvTestError(err.message || 'Environment verification failed');
    } finally {
      setIsVerifyingEnv(false);
    }
  };

  const handleTestPhase53 = async () => {
    if (!hpcPartition.trim()) {
      setPhase53Error('Please enter a SLURM partition name.');
      return;
    }
    setIsTestingPhase53(true);
    setPhase53Error(null);
    setPhase53Result(null);
    try {
      const res = await api.testPhase53HpcRfr(hpcPartition.trim());
      setPhase53Result(res);
    } catch (err: any) {
      setPhase53Error(err.message || 'Phase 5.3 test failed');
    } finally {
      setIsTestingPhase53(false);
    }
  };

  const handlePrepareTest = async () => {
    if (!hpcPartition.trim()) {
      setPrepareError('Please enter a SLURM partition name.');
      return;
    }
    setIsPreparingTest(true);
    setPrepareError(null);
    setPrepareResult(null);
    try {
      const res = await api.preparePhase53Test(hpcPartition.trim());
      setPrepareResult(res);
    } catch (err: any) {
      setPrepareError(err.message || 'Prepare test failed');
    } finally {
      setIsPreparingTest(false);
    }
  };

  // Update sidebar project state
  const updateProject = (overrides: Partial<ProjectState>) => {
    setProject((prev) => ({ ...prev, ...overrides }));
  };

  const handleFileUpload = async (file: File) => {
    try {
      const info = await api.uploadDataset(file);
      onDatasetLoaded(info);
      setResults(null);
      setPlotsGenerated(false);
      setCancelledMsg(null);

      const cols = info.columns;
      const lastCol = cols[cols.length - 1]?.name || '';
      const otherCols = cols.slice(0, -1).map((c) => c.name);

      setTarget(lastCol);
      setSelectedFeatures(otherCols);

      const isReg = cols.find((c) => c.name === lastCol)?.is_numeric ?? true;
      const probType = isReg ? 'Regression' : 'Classification';
      setProblemType(probType);

      updateProject({
        dataset: info.filename,
        rows: info.rows,
        columns: info.columns_count,
        target: lastCol,
        problem: probType,
        features_count: otherCols.length,
        has_results: false,
      });
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    }
  };

  const handleTrain = async () => {
    if (!dataset || !target || selectedFeatures.length === 0) {
      alert('Please configure dataset, target, and features.');
      return;
    }

    if (isTraining) {
      return;
    }

    if (executionMode === 'hpc' && !hpcStatus.connected) {
      setTrainError('Please connect to Supercomputer before training the model.');
      return;
    }

    setIsTraining(true);
    setTrainError(null);
    setCancelledMsg(null);
    setResults(null);
    setPlotsGenerated(false);
    setComparisonAdded(false);

    try {
      const customHp: Record<string, any> = {};
      if (modelName === 'Random Forest') {
        customHp['n_estimators'] = rfTrees;
        customHp['max_depth'] = rfDepth === 0 ? null : rfDepth;
        customHp['min_samples_split'] = rfSplit;
        customHp['min_samples_leaf'] = rfLeaf;
        customHp['max_features'] = rfFeatures === 'None' ? null : rfFeatures;
      }

      const resp = await api.trainExperiment({
        dataset_id: dataset.dataset_id,
        target,
        target_name: target,
        target_unit: targetUnit,
        features: selectedFeatures,
        problem_type: problemType,
        model_name: modelName,
        hyperparameters: customHp,
        split_method: splitMethod,
        train_percent: trainPercent,
        folds,
        repeats,
        optimization,
        opt_iters: optIters,
        opt_cv: optCv,
        use_multiple_seeds: useMultipleSeeds,
        num_seeds: numSeeds,
        use_oob: useOob,
        execution_mode: executionMode,
        partition: hpcPartition || 'cpu_student',
        preprocessing: {
          missing_strategy: missingStrategy,
          encoding_strategy: encodingStrategy,
          scaling_strategy: scalingStrategy,
        },
      });

      const initialStatus: JobStatus = {
        job_id: resp.job_id,
        status: 'running',
        current_stage: 'dataset_prep',
        progress: 'Preparing dataset...',
        started_at: new Date().toLocaleTimeString(),
        elapsed_seconds: 0,
        stages_history: [],
      };
      setJobStatus(initialStatus);

      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const st = await api.getJobStatus(resp.job_id);
          setJobStatus(st);

          if (st.status === 'completed') {
            if (pollRef.current) clearInterval(pollRef.current);
            const res = await api.getJobResults(resp.job_id);
            setResults(res);
            setIsTraining(false);
            updateProject({ has_results: true });

            // Fetch script code for export
            try {
              const codeRes = await fetch(api.getExportScriptUrl(resp.job_id));
              if (codeRes.ok) setScriptCode(await codeRes.text());
            } catch (e) {}
          } else if (st.status === 'cancelled') {
            if (pollRef.current) clearInterval(pollRef.current);
            setIsTraining(false);
            setCancelledMsg(`Cancelled after ${st.elapsed_seconds.toFixed(1)}s`);
            setResults(null);
          } else if (st.status === 'failed') {
            if (pollRef.current) clearInterval(pollRef.current);
            setIsTraining(false);
            setTrainError(st.error || 'Training failed');
          }
        } catch (e) {
          console.error(e);
        }
      }, 1500);
    } catch (err: any) {
      setIsTraining(false);
      setTrainError(err.message || 'Failed to submit training job');
    }
  };

  const handleCancel = async () => {
    if (!jobStatus?.job_id) return;
    try {
      const resp = await api.cancelExperiment(jobStatus.job_id);
      if (pollRef.current) clearInterval(pollRef.current);
      setIsTraining(false);
      setCancelledMsg(`Cancelled after ${resp.elapsed_seconds.toFixed(1)}s`);
      setJobStatus((prev) => prev ? { ...prev, status: 'cancelled', current_stage: 'cancelled' } : null);
      setResults(null);
    } catch (err: any) {
      alert(err.message || 'Failed to cancel experiment');
    }
  };

  const handleAddToComparison = async () => {
    if (!results) return;
    try {
      const data = await api.addToComparison(results.job_id);
      setComparisonAdded(true);
      updateProject({ comparison_runs_count: data.runs_count || 1 });
    } catch (e) {
      console.error(e);
    }
  };

  const availableModels = meta
    ? problemType === 'Regression'
      ? meta.regression_models
      : meta.classification_models
    : [];

  const availablePlotsList = problemType === 'Regression'
    ? ['Actual vs Predicted', 'Residual Plot', 'Residual Distribution', 'Prediction Error', 'Feature Importance']
    : ['Confusion Matrix', 'ROC Curve', 'Precision-Recall Curve', 'Feature Importance', 'Class Distribution'];

  // Define full list of sequential execution stages for Local and HPC
  const LOCAL_STAGES_FLOW = [
    { id: 'dataset_prep', label: 'Preparing dataset' },
    { id: 'split', label: `Train/test split (${trainPercent}/${100 - trainPercent})` },
    ...(optimization !== 'None' && splitMethod === 'Train-Test Split'
      ? [
          { id: 'optimization', label: `${optimization}` },
          { id: 'best_params', label: 'Best parameters selected' },
        ]
      : []),
    { id: 'final_train', label: 'Final model training' },
    { id: 'holdout_eval', label: 'TESTING / HOLDOUT EVALUATION' },
    { id: 'metrics', label: 'Evaluation metrics calculated' },
    { id: 'completed', label: 'Completed' },
  ];

  const HPC_STAGES_FLOW = [
    { id: 'dataset_prep', label: 'Preparing dataset' },
    { id: 'packaging', label: 'Packaging experiment bundle' },
    { id: 'uploading', label: 'Uploading package to Supercomputer' },
    { id: 'submitting', label: 'Submitting job to SLURM scheduler' },
    { id: 'queued', label: 'Job queued in SLURM (Waiting for compute node)' },
    { id: 'running', label: 'Running ML model on compute node' },
    { id: 'downloading', label: 'Retrieving results & metrics from cluster' },
    { id: 'completed', label: 'Completed' },
  ];

  const activeStagesFlow = executionMode === 'hpc' ? HPC_STAGES_FLOW : LOCAL_STAGES_FLOW;
  const currentStageIndex = activeStagesFlow.findIndex((s) => s.id === jobStatus?.current_stage);

  return (
    <div className="space-y-6">
      {/* 1. Upload Dataset */}
      <div>
        <label className="block text-xs font-medium text-[var(--text-primary)] mb-1">Upload Dataset</label>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div
          onClick={() => fileInputRef.current?.click()}
          className="cursor-pointer rounded-lg border border-dashed p-6 text-center transition-colors"
          style={{
            backgroundColor: 'var(--surface)',
            borderColor: 'var(--border)',
          }}
        >
          <UploadCloud className="mx-auto h-8 w-8 text-[var(--text-muted)] mb-2" />
          <p className="text-xs text-[var(--text-primary)] font-medium">
            Drag and drop file here
          </p>
          <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
            Limit 200MB per file • CSV
          </p>
          <button
            type="button"
            className="st-button-secondary mt-3 text-xs py-1 px-3"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Browse files
          </button>
        </div>
      </div>

      {/* When Dataset is Loaded */}
      {dataset && (
        <>
          <StAlert type="success">Dataset Loaded Successfully.</StAlert>

          {/* 3 Metric Columns */}
          <div className="flex flex-wrap gap-4">
            <StMetric label="Rows" value={dataset.rows} />
            <StMetric label="Columns" value={dataset.columns_count} />
            <StMetric label="Duplicates" value={dataset.missing_cells ?? 0} />
          </div>

          {/* Dataset Preview */}
          <div>
            <h3 className="st-subheader">Dataset Preview</h3>
            <div className="st-table-container max-h-56 overflow-auto">
              <table className="st-table">
                <thead>
                  <tr>
                    {dataset.columns.map((c) => (
                      <th key={c.name}>{c.name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataset.preview.map((row, i) => (
                    <tr key={i}>
                      {dataset.columns.map((c) => (
                        <td key={c.name} className="font-mono text-xs">
                          {row[c.name] !== null ? String(row[c.name]) : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Target Variable */}
          <div>
            <h3 className="st-subheader">Target Variable</h3>
            <StSelect
              label="Target Column (Y)"
              value={target}
              onChange={(val) => {
                setTarget(val);
                updateProject({ target: val });
              }}
              options={dataset.columns.map((c) => c.name)}
            />

            <div className="my-2">
              <label className="block text-xs text-[var(--text-primary)] mb-1 font-medium">
                Target Unit (Optional)
              </label>
              <input
                type="text"
                value={targetUnit}
                onChange={(e) => setTargetUnit(e.target.value)}
                placeholder="Example: MPa, °C, %, mm³/Nm, -, HV"
                className="st-input text-xs"
              />
            </div>
          </div>

          {/* Problem Type */}
          <div>
            <StRadio
              label="Select Machine Learning Task"
              options={['Regression', 'Classification']}
              value={problemType}
              onChange={(val) => {
                setProblemType(val);
                updateProject({ problem: val });
              }}
            />
          </div>

          {/* Features Multiselect */}
          <div>
            <StMultiselect
              label="Select Features (X)"
              options={dataset.columns.filter((c) => c.name !== target).map((c) => c.name)}
              selected={selectedFeatures}
              onChange={(val) => {
                setSelectedFeatures(val);
                updateProject({ features_count: val.length });
              }}
            />
          </div>

          {/* Model Configuration Panel */}
          <div>
            <h3 className="st-subheader">Model Configuration</h3>

            <StSelect
              label="Choose Model"
              value={modelName}
              onChange={(val) => {
                setModelName(val);
                updateProject({ model: val });
              }}
              options={availableModels}
            />

            <StSelect
              label="Validation"
              value={splitMethod}
              onChange={(val) => {
                setSplitMethod(val);
                updateProject({ split: val });
              }}
              options={[
                'Train-Test Split',
                'K-Fold Cross Validation',
                'Stratified K-Fold Cross Validation',
                'Repeated K-Fold',
                'Repeated Stratified K-Fold',
              ]}
            />

            {splitMethod === 'Train-Test Split' ? (
              <>
                <StSlider
                  label="Training Percentage (%)"
                  min={50}
                  max={95}
                  step={5}
                  value={trainPercent}
                  onChange={(val) => {
                    setTrainPercent(val);
                    updateProject({ train_percent: val });
                  }}
                  unit="%"
                />
                <StAlert type="info">
                  Training: {trainPercent}% | Testing: {100 - trainPercent}%
                </StAlert>
              </>
            ) : (
              <>
                <StSelect
                  label="Number of Folds"
                  value={folds}
                  onChange={(val) => {
                    setFolds(Number(val));
                    updateProject({ folds: val });
                  }}
                  options={['3', '5', '10']}
                />

                {splitMethod.includes('Repeated') && (
                  <StSelect
                    label="Number of Repeats"
                    value={repeats}
                    onChange={(val) => setRepeats(Number(val))}
                    options={['2', '3', '5', '10']}
                  />
                )}
              </>
            )}

            {/* Hyperparameter Optimization */}
            {splitMethod !== 'Train-Test Split' ? (
              <>
                <StSelect
                  label="Hyperparameter Optimization"
                  value="None"
                  onChange={() => {}}
                  disabled={true}
                  options={['None']}
                />
                <StAlert type="info">
                  Cross Validation with Optimization is disabled to prevent data leakage. Nested CV will be supported in a future release.
                </StAlert>
              </>
            ) : (
              <StSelect
                label="Hyperparameter Optimization"
                value={optimization}
                onChange={(val) => setOptimization(val)}
                options={['None', 'Random Search', 'Grid Search']}
              />
            )}

            {optimization === 'Random Search' && splitMethod === 'Train-Test Split' && (
              <>
                <StSlider
                  label="Random Search Iterations"
                  min={5}
                  max={100}
                  step={5}
                  value={optIters}
                  onChange={(val) => setOptIters(val)}
                />
                <StSelect
                  label="Optimization CV Folds"
                  value={optCv}
                  onChange={(val) => setOptCv(Number(val))}
                  options={['2', '3', '5']}
                />
              </>
            )}

            {optimization === 'Grid Search' && splitMethod === 'Train-Test Split' && (
              <StSelect
                label="Optimization CV Folds"
                value={optCv}
                onChange={(val) => setOptCv(Number(val))}
                options={['2', '3', '5']}
              />
            )}

            {/* Multiple Random Seeds */}
            <div className="my-2 flex items-center space-x-2">
              <input
                type="checkbox"
                id="multi-seed-check"
                checked={useMultipleSeeds}
                onChange={(e) => setUseMultipleSeeds(e.target.checked)}
                className="h-3.5 w-3.5"
                style={{ accentColor: 'var(--accent)' }}
              />
              <label htmlFor="multi-seed-check" className="text-xs text-[var(--text-primary)] cursor-pointer">
                Multiple Random Seed Evaluation
              </label>
            </div>

            {useMultipleSeeds && (
              <StSelect
                label="Number of Seeds"
                value={numSeeds}
                onChange={(val) => setNumSeeds(Number(val))}
                options={['5', '10', '20', '50']}
              />
            )}

            {/* Random Forest OOB */}
            {modelName === 'Random Forest' && (
              <div className="my-2 flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="oob-check"
                  checked={useOob}
                  onChange={(e) => setUseOob(e.target.checked)}
                  className="h-3.5 w-3.5"
                  style={{ accentColor: 'var(--accent)' }}
                />
                <label htmlFor="oob-check" className="text-xs text-[var(--text-primary)] cursor-pointer">
                  Enable OOB Score (Out-of-Bag)
                </label>
              </div>
            )}

            {/* Advanced Settings Expander */}
            <StExpander title="Advanced Settings">
              {modelName === 'Random Forest' && (
                <div className="space-y-2">
                  <StSlider
                    label="Number of Trees"
                    min={50}
                    max={1000}
                    step={50}
                    value={rfTrees}
                    onChange={(val) => setRfTrees(val)}
                  />
                  <div className="my-2">
                    <label className="block text-xs text-[var(--text-primary)] mb-1">
                      Maximum Depth (0 = None)
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={rfDepth}
                      onChange={(e) => setRfDepth(Number(e.target.value))}
                      className="st-input text-xs"
                    />
                  </div>
                  <StSlider
                    label="Minimum Samples Split"
                    min={2}
                    max={20}
                    step={1}
                    value={rfSplit}
                    onChange={(val) => setRfSplit(val)}
                  />
                  <StSlider
                    label="Minimum Samples Leaf"
                    min={1}
                    max={20}
                    step={1}
                    value={rfLeaf}
                    onChange={(val) => setRfLeaf(val)}
                  />
                  <StSelect
                    label="Maximum Features"
                    value={rfFeatures}
                    onChange={(val) => setRfFeatures(val)}
                    options={['sqrt', 'log2', 'None']}
                  />
                </div>
              )}
            </StExpander>
          </div>

          {/* Preprocessing Panel */}
          <div>
            <h3 className="st-subheader">Preprocessing</h3>

            <StSelect
              label="Missing Value Strategy"
              value={missingStrategy}
              onChange={(val) => setMissingStrategy(val)}
              options={['None', 'Mean', 'Median', 'Most Frequent']}
            />

            <StSelect
              label="Encoding Strategy"
              value={encodingStrategy}
              onChange={(val) => setEncodingStrategy(val)}
              options={['None', 'One-Hot', 'Ordinal']}
            />

            <StSelect
              label="Scaling Strategy"
              value={scalingStrategy}
              onChange={(val) => setScalingStrategy(val)}
              options={['None', 'StandardScaler', 'MinMaxScaler', 'RobustScaler']}
            />
          </div>

          <div className="st-divider" />

          {/* Execution Control & Action Buttons */}
          <div>
            {/* Execution Mode Selector */}
            <div className="mb-3">
              <label className="st-label mb-1.5">Execution Mode</label>
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-1.5 cursor-pointer text-xs">
                  <input
                    type="radio"
                    name="execution_mode"
                    value="local"
                    checked={executionMode === 'local'}
                    onChange={() => setExecutionMode('local')}
                    className="accent-[#ff4b4b]"
                  />
                  <span className={executionMode === 'local' ? 'font-semibold' : ''}>Local Machine</span>
                </label>
                <label className="flex items-center space-x-1.5 cursor-pointer text-xs">
                  <input
                    type="radio"
                    name="execution_mode"
                    value="hpc"
                    checked={executionMode === 'hpc'}
                    onChange={() => setExecutionMode('hpc')}
                    className="accent-[#ff4b4b]"
                  />
                  <span className={executionMode === 'hpc' ? 'font-semibold' : ''}>Supercomputer</span>
                </label>
              </div>
              {/* Supercomputer Connection Panel */}
              {executionMode === 'hpc' && (
                <div className="mt-3 p-3 border border-border/80 rounded-md bg-muted/20 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Server className="h-4 w-4 text-muted-foreground" />
                      <span className="text-xs font-medium">Supercomputer:</span>
                      {hpcStatus.connected ? (
                        <span className="inline-flex items-center text-xs font-semibold text-green-600 dark:text-green-400 bg-green-500/10 px-2 py-0.5 rounded">
                          ● Connected
                        </span>
                      ) : (
                        <span className="inline-flex items-center text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                          ○ Not Connected
                        </span>
                      )}
                    </div>

                    {hpcStatus.connected ? (
                      <button
                        type="button"
                        onClick={handleDisconnectHpc}
                        className="text-xs px-2.5 py-1 bg-muted hover:bg-muted/80 text-foreground rounded border border-border/60 transition-colors"
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={handleConnectHpc}
                        disabled={isConnectingHpc || (hpcMode === 'ssh' && (!hpcHost || !hpcUsername))}
                        className="text-xs px-3 py-1 bg-[#ff4b4b] hover:bg-[#e03a3a] disabled:opacity-50 text-white rounded font-medium transition-colors flex items-center space-x-1"
                      >
                        {isConnectingHpc ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wifi className="h-3 w-3" />}
                        <span>{isConnectingHpc ? 'Connecting...' : 'Connect'}</span>
                      </button>
                    )}
                  </div>

                  {/* Connected Details & Partition Configuration */}
                  {hpcStatus.connected && (
                    <div className="space-y-3 pt-2 border-t border-border/40">
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
                        <div>
                          <span className="font-medium text-foreground">Host: </span>
                          <span className="font-mono">{hpcStatus.host || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="font-medium text-foreground">User: </span>
                          <span className="font-mono">{hpcStatus.username || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="font-medium text-foreground">Login Node: </span>
                          <span className="font-mono">{hpcStatus.node || 'login-node'}</span>
                        </div>
                        <div>
                          <span className="font-medium text-foreground">Authentication: </span>
                          <span>{hpcStatus.auth_type || 'SSH Key'}</span>
                        </div>
                      </div>

                      {/* SLURM Partition Selection (Production User Control) */}
                      <div className="pt-2 border-t border-border/30 space-y-1">
                        <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                          <span>SLURM Partition</span>
                          <span className="text-[10px] font-normal text-muted-foreground">Default: cpu_student</span>
                        </label>
                        <div className="flex items-center space-x-2">
                          <input
                            type="text"
                            value={hpcPartition}
                            onChange={(e) => setHpcPartition(e.target.value)}
                            placeholder="e.g. cpu_student"
                            className="w-full text-xs px-2.5 py-1.5 bg-background border border-border rounded font-mono"
                          />
                        </div>
                        <p className="text-[11px] text-muted-foreground">
                          Jobs are scheduled on this partition with 2 CPUs and 2 GB memory limit.
                        </p>
                      </div>

                      {/* Advanced / HPC Diagnostics (Expandable) */}
                      <div className="pt-2 border-t border-border/30">
                        <StExpander title="🛠️ Advanced / HPC Diagnostics">
                          <div className="space-y-3 text-xs">
                            <p className="text-muted-foreground text-[11px]">
                              Internal diagnostics to verify cluster file transfer, SLURM scheduling, compute node Python environment, and benchmark packaging without affecting your dataset.
                            </p>

                            <div className="flex flex-wrap gap-2 pt-1">
                              <button
                                type="button"
                                onClick={handleTestFileTransfer}
                                disabled={isTestingTransfer}
                                className="text-xs px-2.5 py-1 bg-muted hover:bg-muted/80 text-foreground border border-border/60 rounded font-medium transition-colors flex items-center space-x-1.5"
                              >
                                {isTestingTransfer ? <Loader2 className="h-3 w-3 animate-spin text-[#ff4b4b]" /> : <FileCheck className="h-3 w-3 text-muted-foreground" />}
                                <span>{isTestingTransfer ? 'Testing...' : 'Test File Transfer'}</span>
                              </button>

                              <button
                                type="button"
                                onClick={handleTestSlurmJob}
                                disabled={isTestingSlurm || !hpcPartition.trim()}
                                className="text-xs px-2.5 py-1 bg-muted hover:bg-muted/80 disabled:opacity-50 text-foreground border border-border/60 rounded font-medium transition-colors flex items-center space-x-1.5 whitespace-nowrap"
                              >
                                {isTestingSlurm ? <Loader2 className="h-3 w-3 animate-spin text-[#ff4b4b]" /> : <Terminal className="h-3 w-3 text-muted-foreground" />}
                                <span>{isTestingSlurm ? 'Testing...' : 'Test SLURM'}</span>
                              </button>

                              <button
                                type="button"
                                onClick={handleVerifyEnv}
                                disabled={isVerifyingEnv || !hpcPartition.trim()}
                                className="text-xs px-2.5 py-1 bg-muted hover:bg-muted/80 disabled:opacity-50 text-foreground border border-border/60 rounded font-medium transition-colors flex items-center space-x-1.5 whitespace-nowrap"
                              >
                                {isVerifyingEnv ? <Loader2 className="h-3 w-3 animate-spin text-[#ff4b4b]" /> : <Server className="h-3 w-3 text-muted-foreground" />}
                                <span>{isVerifyingEnv ? 'Checking...' : 'Verify Python Env'}</span>
                              </button>

                              <button
                                type="button"
                                onClick={handlePrepareTest}
                                disabled={isPreparingTest || !hpcPartition.trim()}
                                className="text-xs px-2.5 py-1 bg-muted hover:bg-muted/80 disabled:opacity-50 text-foreground border border-border/60 rounded font-medium transition-colors flex items-center space-x-1.5 whitespace-nowrap"
                              >
                                {isPreparingTest ? <Loader2 className="h-3 w-3 animate-spin text-[#ff4b4b]" /> : <FolderUp className="h-3 w-3 text-muted-foreground" />}
                                <span>{isPreparingTest ? 'Uploading...' : 'Prepare HPC Test Files'}</span>
                              </button>

                              <button
                                type="button"
                                onClick={handleTestPhase53}
                                disabled={isTestingPhase53 || !hpcPartition.trim()}
                                className="text-xs px-2.5 py-1 bg-muted hover:bg-muted/80 disabled:opacity-50 text-foreground border border-border/60 rounded font-medium transition-colors flex items-center space-x-1.5 whitespace-nowrap"
                              >
                                {isTestingPhase53 ? <Loader2 className="h-3 w-3 animate-spin text-[#ff4b4b]" /> : <CheckCircle2 className="h-3 w-3 text-muted-foreground" />}
                                <span>{isTestingPhase53 ? 'Testing ML...' : 'Test HPC ML (Phase 5.3)'}</span>
                              </button>
                            </div>

                            {/* File Transfer Success Display */}
                            {transferTestResult && (
                              <div className="p-2.5 bg-green-500/10 border border-green-500/30 rounded text-xs text-foreground space-y-1">
                                <div className="font-semibold text-green-600 dark:text-green-400 flex items-center space-x-1">
                                  <span>✓ File transfer test successful</span>
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-muted-foreground pt-0.5">
                                  <div>Upload: <span className="font-medium text-foreground">{transferTestResult.steps.upload}</span></div>
                                  <div>Remote verify: <span className="font-medium text-foreground">{transferTestResult.steps.remote_verify}</span></div>
                                  <div>Download: <span className="font-medium text-foreground">{transferTestResult.steps.download}</span></div>
                                  <div>Content verify: <span className="font-medium text-foreground">{transferTestResult.steps.content_verify}</span></div>
                                  <div className="col-span-2">Cleanup: <span className="font-medium text-foreground">{transferTestResult.steps.cleanup}</span></div>
                                </div>
                              </div>
                            )}

                            {/* File Transfer Error Display */}
                            {transferTestError && (
                              <div className="p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-500 dark:text-red-400">
                                {transferTestError}
                              </div>
                            )}

                            {/* Prepare Test Files Success Display */}
                            {prepareResult && (
                              <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/30 rounded text-xs text-foreground space-y-1">
                                <div className="font-semibold text-cyan-600 dark:text-cyan-400 flex items-center justify-between">
                                  <span>✓ HPC Test Files Prepared (Inspection Mode)</span>
                                  <span className="text-[10px] font-mono text-muted-foreground">sbatch not executed</span>
                                </div>
                                <div className="text-[11px] text-muted-foreground pt-0.5 space-y-1">
                                  <div>Remote Path: <code className="font-mono text-foreground font-semibold bg-muted px-1 py-0.5 rounded select-all">{prepareResult.remote_workspace}</code></div>
                                  <div>Uploaded Files: <span className="font-mono text-foreground">{prepareResult.files?.join(', ')}</span></div>
                                  <div>Configured: <span className="font-mono text-foreground">{prepareResult.cpus_per_task} CPUs, {prepareResult.mem} RAM, {prepareResult.time_limit} limit, partition {prepareResult.partition}</span></div>
                                  <div className="text-[10px] text-muted-foreground pt-0.5 italic">Workspace left intact for inspection via SSH.</div>
                                </div>
                              </div>
                            )}

                            {/* Prepare Test Files Error Display */}
                            {prepareError && (
                              <div className="p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-500 dark:text-red-400">
                                {prepareError}
                              </div>
                            )}

                            {/* SLURM Test Success Display */}
                            {slurmTestResult && (
                              <div className="p-2.5 bg-green-500/10 border border-green-500/30 rounded text-xs text-foreground space-y-1">
                                <div className="font-semibold text-green-600 dark:text-green-400 flex items-center space-x-1">
                                  <span>✓ SLURM test successful</span>
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-muted-foreground pt-0.5">
                                  <div>Job ID: <span className="font-medium text-foreground">{slurmTestResult.job_id}</span></div>
                                  <div>Partition: <span className="font-medium text-foreground">{slurmTestResult.partition}</span></div>
                                  <div>Status: <span className="font-medium text-foreground">{slurmTestResult.status}</span></div>
                                  <div>Output verification: <span className="font-medium text-foreground">{slurmTestResult.steps.output_verify}</span></div>
                                  <div className="col-span-2">Cleanup: <span className="font-medium text-foreground">{slurmTestResult.steps.cleanup}</span></div>
                                </div>
                              </div>
                            )}

                            {/* SLURM Test Error Display */}
                            {slurmTestError && (
                              <div className="p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-500 dark:text-red-400">
                                {slurmTestError}
                              </div>
                            )}

                            {/* Compute Node Environment Result Display */}
                            {envTestResult && (
                              <div className="p-2.5 bg-blue-500/10 border border-blue-500/30 rounded text-xs text-foreground space-y-1">
                                <div className="font-semibold text-blue-600 dark:text-blue-400 flex items-center space-x-1">
                                  <span>✓ Compute Node Environment Verified</span>
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-muted-foreground pt-0.5 font-mono">
                                  <div>Node: <span className="font-medium text-foreground">{envTestResult.hostname}</span></div>
                                  <div>Python: <span className="font-medium text-foreground">{envTestResult.python_version}</span></div>
                                  <div>numpy: <span className="font-medium text-foreground">{envTestResult.numpy}</span></div>
                                  <div>pandas: <span className="font-medium text-foreground">{envTestResult.pandas}</span></div>
                                  <div>scikit-learn: <span className="font-medium text-foreground">{envTestResult.scikit_learn}</span></div>
                                  <div>xgboost: <span className="font-medium text-foreground">{envTestResult.xgboost}</span></div>
                                  <div>catboost: <span className="font-medium text-foreground">{envTestResult.catboost}</span></div>
                                  <div className="col-span-2 text-[10px] text-muted-foreground truncate font-sans">
                                    Path: {envTestResult.python}
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Compute Node Environment Error Display */}
                            {envTestError && (
                              <div className="p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-500 dark:text-red-400">
                                {envTestError}
                              </div>
                            )}

                            {/* Phase 5.3 Test ML Job Result Display */}
                            {phase53Result && (
                              <div className="p-2.5 bg-purple-500/10 border border-purple-500/30 rounded text-xs text-foreground space-y-1">
                                <div className="font-semibold text-purple-600 dark:text-purple-400 flex items-center justify-between">
                                  <span>✓ Real HPC ML Benchmark: PASS</span>
                                  <span className="text-[10px] font-mono text-muted-foreground">Job #{phase53Result.slurm_job_id}</span>
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-muted-foreground pt-0.5 font-mono">
                                  <div>Compute Node: <span className="font-medium text-foreground">{phase53Result.compute_node}</span></div>
                                  <div>Partition: <span className="font-medium text-foreground">{phase53Result.partition}</span></div>
                                  <div>HPC Time: <span className="font-medium text-foreground">{phase53Result.hpc_training_time?.toFixed(2)}s</span></div>
                                  <div>Local Time: <span className="font-medium text-foreground">{phase53Result.local_training_time?.toFixed(2)}s</span></div>
                                  <div>HPC R² Score: <span className="font-medium text-green-500">{phase53Result.hpc_metrics?.['R2 Score']?.toFixed(4)}</span></div>
                                  <div>Local R² Score: <span className="font-medium text-green-500">{phase53Result.local_metrics?.['R2 Score']?.toFixed(4)}</span></div>
                                  <div className="col-span-2">R² Delta: <span className="font-medium text-foreground">{phase53Result.r2_delta?.toFixed(6)}</span></div>
                                  <div className="col-span-2">Workspace Cleanup: <span className="font-medium text-green-500">{phase53Result.cleanup}</span></div>
                                </div>
                              </div>
                            )}

                            {/* Phase 5.3 Error Display */}
                            {phase53Error && (
                              <div className="p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-500 dark:text-red-400">
                                {phase53Error}
                              </div>
                            )}
                          </div>
                        </StExpander>
                      </div>
                    </div>
                  )}

                  {/* Disconnected Form */}
                  {!hpcStatus.connected && (
                    <div className="space-y-2.5 pt-1 border-t border-border/40">
                      <div className="flex items-center space-x-3 text-xs">
                        <label className="flex items-center space-x-1 cursor-pointer">
                          <input
                            type="radio"
                            name="hpc_submode"
                            value="mock"
                            checked={hpcMode === 'mock'}
                            onChange={() => setHpcMode('mock')}
                            className="accent-[#ff4b4b]"
                          />
                          <span>Mock HPC (Offline Simulation)</span>
                        </label>
                        <label className="flex items-center space-x-1 cursor-pointer">
                          <input
                            type="radio"
                            name="hpc_submode"
                            value="ssh"
                            checked={hpcMode === 'ssh'}
                            onChange={() => setHpcMode('ssh')}
                            className="accent-[#ff4b4b]"
                          />
                          <span>Remote HPC (SSH Key/Agent)</span>
                        </label>
                      </div>

                      {hpcMode === 'ssh' && (
                        <div className="space-y-2 pt-1">
                          <div className="grid grid-cols-5 gap-2">
                            <div className="col-span-2">
                              <label className="text-[11px] text-muted-foreground block mb-0.5">Host</label>
                              <input
                                type="text"
                                value={hpcHost}
                                onChange={(e) => setHpcHost(e.target.value)}
                                placeholder="e.g. cluster.univ.edu"
                                className="w-full text-xs px-2 py-1 bg-background border border-border rounded"
                              />
                            </div>
                            <div className="col-span-2">
                              <label className="text-[11px] text-muted-foreground block mb-0.5">Username</label>
                              <input
                                type="text"
                                value={hpcUsername}
                                onChange={(e) => setHpcUsername(e.target.value)}
                                placeholder="e.g. username"
                                className="w-full text-xs px-2 py-1 bg-background border border-border rounded"
                              />
                            </div>
                            <div className="col-span-1">
                              <label className="text-[11px] text-muted-foreground block mb-0.5">Port</label>
                              <input
                                type="number"
                                value={hpcPort}
                                onChange={(e) => setHpcPort(Number(e.target.value))}
                                className="w-full text-xs px-2 py-1 bg-background border border-border rounded"
                              />
                            </div>
                          </div>

                          <div className="space-y-1">
                            <label className="text-[11px] text-muted-foreground block mb-0.5">
                              SSH Key Passphrase <span className="text-[10px] opacity-75">(if ~/.ssh/id_ed25519 is encrypted)</span>
                            </label>
                            <input
                              type="password"
                              value={hpcPassphrase}
                              onChange={(e) => setHpcPassphrase(e.target.value)}
                              placeholder="Enter passphrase for local SSH key"
                              className="w-full text-xs px-2 py-1 bg-background border border-border rounded"
                            />
                            <div className="text-[10px] text-muted-foreground">
                              This is the passphrase protecting your local SSH key, not your HPC account password.
                            </div>
                          </div>

                          <div className="text-[11px] text-muted-foreground">
                            Authentication: Uses your existing SSH keys (<code className="text-[10px]">~/.ssh</code>) directly. Solvosys never requests or stores your account password.
                          </div>
                        </div>
                      )}

                      {hpcError && (
                        <div className="text-xs text-red-500 dark:text-red-400">
                          {hpcError}
                        </div>
                      )}
                    </div>
                  )}

                  {/* HPC SSH Setup Guide (Expandable) */}
                  <div className="pt-2 border-t border-border/40">
                    <StExpander title="📖 How to set up SSH access (HPC SSH Setup Guide)">
                      <div className="space-y-3.5 text-xs text-muted-foreground leading-relaxed">
                        {/* 1. Prerequisites */}
                        <div>
                          <div className="font-semibold text-foreground text-[12px] mb-1">
                            1. Prerequisites
                          </div>
                          <ul className="list-disc pl-4 space-y-1">
                            <li>Solvosys requires <strong>SSH-key authentication</strong> for Remote HPC execution.</li>
                            <li>A <strong>passphrase</strong> is recommended to protect your local private key.</li>
                            <li>If your key is passphrase-protected, Solvosys will request the passphrase during connection (used in-memory only).</li>
                            <li>Solvosys <strong>never requires, requests, or stores</strong> your university/HPC account password.</li>
                          </ul>
                        </div>

                        {/* 2. Check for an existing key */}
                        <div>
                          <div className="font-semibold text-foreground text-[12px] mb-1">
                            2. Check for an existing SSH key
                          </div>
                          <p className="mb-1.5">Open PowerShell on your Windows PC and check your <code className="text-[11px] bg-muted px-1 py-0.5 rounded">.ssh</code> folder:</p>
                          <div className="bg-background border border-border/70 rounded p-2 font-mono text-[11px] select-all text-foreground">
                            Get-ChildItem "$HOME\.ssh"
                          </div>
                          <p className="mt-1 text-[11px]">
                            Common key pairs include <code className="text-[11px] bg-muted px-1 py-0.5 rounded">id_ed25519</code> (private) and <code className="text-[11px] bg-muted px-1 py-0.5 rounded">id_ed25519.pub</code> (public).
                          </p>
                        </div>

                        {/* 3. Create an SSH key if none exists */}
                        <div>
                          <div className="font-semibold text-foreground text-[12px] mb-1">
                            3. Create an SSH key if you do not have one
                          </div>
                          <p className="mb-1.5">Generate a secure Ed25519 key pair in PowerShell:</p>
                          <div className="bg-background border border-border/70 rounded p-2 font-mono text-[11px] select-all text-foreground">
                            ssh-keygen -t ed25519 -C "your_hpc_username@hpc"
                          </div>
                          <ul className="list-disc pl-4 space-y-1 mt-1.5">
                            <li>Press <strong>Enter</strong> to accept the default file location (<code className="text-[10px]">~/.ssh/id_ed25519</code>).</li>
                            <li>Create a strong passphrase to encrypt your private key.</li>
                            <li><strong>Keep <code className="text-[10px]">id_ed25519</code> strictly private</strong> — never share, paste, or upload it.</li>
                            <li>The <code className="text-[10px]">.pub</code> file (<code className="text-[10px]">id_ed25519.pub</code>) is your public key.</li>
                          </ul>
                        </div>

                        {/* 4. Authorize the public key */}
                        <div>
                          <div className="font-semibold text-foreground text-[12px] mb-1">
                            4. Authorize the public key on your HPC account
                          </div>
                          <p>
                            Add your public key (<code className="text-[11px] bg-muted px-1 py-0.5 rounded">id_ed25519.pub</code>) to your HPC account using your cluster or university's approved SSH-key setup procedure.
                          </p>
                        </div>

                        {/* 5. Test SSH access */}
                        <div>
                          <div className="font-semibold text-foreground text-[12px] mb-1">
                            5. Test SSH access from your terminal
                          </div>
                          <p className="mb-1.5">Verify that your key connects successfully in PowerShell:</p>
                          <div className="bg-background border border-border/70 rounded p-2 font-mono text-[11px] select-all text-foreground">
                            ssh your_username@your_hpc_host
                          </div>
                          <p className="mt-1 text-[11px]">
                            You may be prompted to enter your local SSH key passphrase.
                          </p>
                        </div>

                        {/* 6. Use Solvosys */}
                        <div>
                          <div className="font-semibold text-foreground text-[12px] mb-1">
                            6. Connect from Solvosys
                          </div>
                          <ol className="list-decimal pl-4 space-y-1">
                            <li>Select <strong>Execution Mode → Supercomputer</strong>.</li>
                            <li>Select <strong>Remote HPC (SSH Key/Agent)</strong>.</li>
                            <li>Enter your cluster <strong>Host</strong>, <strong>Username</strong>, and <strong>Port</strong> (default: 22).</li>
                            <li>Enter your <strong>SSH Key Passphrase</strong> when prompted.</li>
                            <li>Click <strong>Connect</strong>.</li>
                          </ol>
                        </div>

                        {/* 7. Security note */}
                        <div className="p-2.5 bg-blue-500/10 border border-blue-500/30 rounded text-foreground text-[11px] space-y-1">
                          <div className="font-semibold text-blue-500 flex items-center space-x-1">
                            <span>🔒 Security Summary</span>
                          </div>
                          <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground text-[11px]">
                            <li>Your private key stays 100% local on your PC.</li>
                            <li>Solvosys never asks for or handles your HPC account password.</li>
                            <li>Solvosys does not store or write your SSH-key passphrase to disk.</li>
                            <li>Never paste, email, or upload your private key. Only the public key (<code className="text-[10px]">.pub</code>) is registered with the HPC.</li>
                          </ul>
                        </div>
                      </div>
                    </StExpander>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={handleTrain}
                disabled={isTraining || selectedFeatures.length === 0}
                className="st-button-primary flex-1 py-2.5 flex items-center justify-center space-x-2"
              >
                {isTraining ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Training Model ({jobStatus?.elapsed_seconds?.toFixed(1) ?? '0.0'}s)...</span>
                  </>
                ) : (
                  <span>Train Model</span>
                )}
              </button>

              {/* STOP TRAINING BUTTON */}
              {isTraining && (
                <button
                  type="button"
                  onClick={handleCancel}
                  className="bg-[#d93025] hover:bg-[#b3261e] text-white font-semibold px-5 py-2.5 rounded-md text-xs flex items-center space-x-1.5 transition-colors shadow-sm"
                >
                  <Square className="h-3.5 w-3.5 fill-current" />
                  <span>STOP TRAINING</span>
                </button>
              )}
            </div>

            {/* EXPERIMENT STATUS PANEL */}
            {isTraining && jobStatus && (
              <div
                className="mt-4 p-4 rounded-lg border text-xs space-y-3"
                style={{
                  backgroundColor: 'var(--surface)',
                  borderColor: 'var(--border)',
                }}
              >
                <div className="flex items-center justify-between border-b pb-2" style={{ borderColor: 'var(--border)' }}>
                  <span className="font-bold uppercase tracking-wider text-[var(--text-primary)]">
                    Experiment Status
                  </span>
                  <div className="flex items-center space-x-3 text-[11px] text-[var(--text-muted)]">
                    {jobStatus.started_at && <span>Started: {jobStatus.started_at}</span>}
                    <span>Elapsed: {jobStatus.elapsed_seconds?.toFixed(1)}s</span>
                  </div>
                </div>

                {/* HPC Supercomputer SLURM Status Banner */}
                {executionMode === 'hpc' && (
                  <div className="p-3 rounded bg-purple-500/10 border border-purple-500/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Server className="h-4 w-4 text-purple-400" />
                        <span className="font-semibold text-purple-400 text-xs">Supercomputer SLURM Job</span>
                      </div>
                      {jobStatus.slurm_job_id && (
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-semibold border border-purple-500/30">
                          Job #{jobStatus.slurm_job_id}
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[11px] font-mono pt-1 text-muted-foreground border-t border-purple-500/20">
                      <div>
                        <span className="text-foreground font-medium">Partition: </span>
                        <span>{jobStatus.partition || hpcPartition || 'cpu_student'}</span>
                      </div>
                      <div>
                        <span className="text-foreground font-medium">State: </span>
                        <span className="font-semibold text-purple-300">{jobStatus.slurm_state || (jobStatus.current_stage === 'queued' ? 'PENDING' : 'RUNNING')}</span>
                      </div>
                      <div>
                        <span className="text-foreground font-medium">Compute Node: </span>
                        <span className="text-foreground">{jobStatus.compute_node || (jobStatus.current_stage === 'queued' ? 'Waiting...' : 'dgxa')}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Prominent Stage 6 Holdout Testing Alert (Local Mode) */}
                {executionMode === 'local' && jobStatus.current_stage === 'holdout_eval' && (
                  <div className="p-2.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-400 font-semibold flex items-center space-x-2">
                    <CircleDot className="h-4 w-4 animate-pulse shrink-0" />
                    <span>Testing model on holdout test set ({100 - trainPercent}%)...</span>
                  </div>
                )}

                {/* Prominent HPC Queued Alert */}
                {executionMode === 'hpc' && jobStatus.current_stage === 'queued' && (
                  <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold flex items-center space-x-2">
                    <Clock className="h-4 w-4 animate-pulse shrink-0 text-amber-400" />
                    <span>Job is queued in partition '{jobStatus.partition || hpcPartition || 'cpu_student'}'. Waiting for SLURM compute node allocation...</span>
                  </div>
                )}

                {/* Prominent HPC Running Alert */}
                {executionMode === 'hpc' && jobStatus.current_stage === 'running' && (
                  <div className="p-2.5 rounded bg-green-500/10 border border-green-500/30 text-green-400 font-semibold flex items-center space-x-2">
                    <CircleDot className="h-4 w-4 animate-pulse shrink-0 text-green-400" />
                    <span>Running ML model on compute node {jobStatus.compute_node ? `(${jobStatus.compute_node})` : ''}...</span>
                  </div>
                )}

                {/* Sequential Stage Tracker */}
                <div className="space-y-1.5 pt-1">
                  {activeStagesFlow.map((stage, idx) => {
                    const isCompleted = currentStageIndex > idx || jobStatus.status === 'completed';
                    const isActive = currentStageIndex === idx && jobStatus.status === 'running';

                    return (
                      <div
                        key={stage.id}
                        className={`flex items-center space-x-2 py-0.5 ${
                          isActive
                            ? 'font-bold text-[var(--accent)]'
                            : isCompleted
                            ? 'text-[var(--text-primary)]'
                            : 'text-[var(--text-muted)] opacity-60'
                        }`}
                      >
                        {isCompleted ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0" />
                        ) : isActive ? (
                          <CircleDot className="h-3.5 w-3.5 text-[var(--accent)] animate-pulse shrink-0" />
                        ) : (
                          <Circle className="h-3.5 w-3.5 shrink-0" />
                        )}
                        <span>{stage.label}</span>
                      </div>
                    );
                  })}
                </div>

                {/* Fit-level optimization info */}
                {jobStatus.optimization_info && (
                  <div className="mt-2 p-2.5 rounded bg-[var(--sidebar-bg)] border border-[var(--border)] space-y-1">
                    <p className="font-semibold text-[var(--text-primary)]">
                      {jobStatus.optimization_info.strategy} Progress
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)]">
                      {jobStatus.optimization_info.iterations} iterations × {jobStatus.optimization_info.folds} CV folds = {jobStatus.optimization_info.total_fits} total fits on {jobStatus.optimization_info.rows} training rows
                    </p>
                    {jobStatus.best_cv_score !== undefined && jobStatus.best_cv_score !== null && (
                      <p className="text-[11px] text-green-400 font-semibold">
                        Best CV {problemType === 'Regression' ? 'R²' : 'Score'}: {jobStatus.best_cv_score.toFixed(4)}
                      </p>
                    )}
                  </div>
                )}

                {/* Best Parameters Preview if optimization finished */}
                {jobStatus.best_params && (
                  <div className="p-2.5 rounded bg-[var(--sidebar-bg)] border border-[var(--border)] text-[11px]">
                    <p className="font-semibold text-green-400 mb-1">✓ Hyperparameter optimization completed</p>
                    <p className="text-[var(--text-muted)]">Best Parameters:</p>
                    <pre className="font-mono text-[10px] text-[var(--text-primary)] mt-0.5 overflow-x-auto">
                      {JSON.stringify(jobStatus.best_params, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {cancelledMsg && (
              <div className="mt-3">
                <StAlert type="warning">{cancelledMsg}</StAlert>
              </div>
            )}

            {trainError && (
              <div className="mt-3">
                <StAlert type="error">{trainError}</StAlert>
              </div>
            )}
          </div>

          {/* Results Section */}
          {results && (
            <div>
              <StAlert type="success">
                Model Trained Successfully in {results.training_time?.toFixed(2) ?? results.total_elapsed?.toFixed(2)}s.
                {'\n'}Holdout testing completed.
              </StAlert>
              <div className="st-divider" />

              {/* Evaluation Protocol Badge */}
              <StAlert type="info">
                <strong>Evaluation Protocol</strong>
                {'\n\n'}
                <strong>Validation</strong>: {results.evaluation_config?.validation || 'Train-Test Split'}
                {'\n'}
                <strong>Optimization</strong>: {results.evaluation_config?.optimization || 'None'}
                {results.evaluation_config?.best_cv_score !== undefined && results.evaluation_config?.best_cv_score !== null && (
                  <>
                    {'\n'}
                    <strong>Best CV {problemType === 'Regression' ? 'R²' : 'Score'}</strong>: {Number(results.evaluation_config.best_cv_score).toFixed(4)}
                  </>
                )}
                {results.model_name === 'Random Forest' && (
                  <>
                    {'\n'}
                    <strong>Random Forest OOB</strong>: {results.evaluation_config?.oob ? (
                      results.evaluation_config?.oob_score !== undefined && results.evaluation_config?.oob_score !== null
                        ? `Enabled (OOB ${problemType === 'Regression' ? 'R²' : 'Score'}: ${Number(results.evaluation_config.oob_score).toFixed(4)})`
                        : 'Enabled'
                    ) : 'Disabled'}
                  </>
                )}
                {'\n'}
                <strong>Random State</strong>: {results.evaluation_config?.random_state ?? 42}
                {results.best_params && (
                  <>
                    {'\n\n'}
                    <strong>Best Hyperparameters</strong>:
                    {'\n'}
                    {Object.entries(results.best_params).map(([k, v]) => `• ${k} = ${v}`).join('\n')}
                  </>
                )}
              </StAlert>

              {/* Evaluation Results Metrics */}
              <h3 className="st-subheader mt-4">
                Evaluation Results {splitMethod === 'Train-Test Split' ? '(Holdout Test Set)' : '(Cross-Validation)'}
              </h3>
              <div className="flex flex-wrap gap-4 my-3">
                {problemType === 'Regression' ? (
                  <>
                    <StMetric
                      label={splitMethod === 'Train-Test Split' ? "Holdout Test R²" : "CV R² Score"}
                      value={formatMetric(results.metrics?.['R2 Score'])}
                    />
                    <StMetric
                      label={splitMethod === 'Train-Test Split' ? "Holdout Test RMSE" : "CV RMSE"}
                      value={formatMetric(results.metrics?.['RMSE'])}
                    />
                    <StMetric
                      label={splitMethod === 'Train-Test Split' ? "Holdout Test MAE" : "CV MAE"}
                      value={formatMetric(results.metrics?.['MAE'])}
                    />
                    <StMetric
                      label={splitMethod === 'Train-Test Split' ? "Holdout Test MAPE" : "CV MAPE"}
                      value={formatMetric(results.metrics?.['MAPE'], true)}
                    />
                    {(results.metrics?.['OOB Score'] !== undefined || results.oob_score !== undefined) && (
                      <StMetric
                        label="Random Forest OOB R²"
                        value={formatMetric(results.metrics?.['OOB Score'] ?? results.oob_score)}
                      />
                    )}
                  </>
                ) : (
                  <>
                    <StMetric
                      label={splitMethod === 'Train-Test Split' ? "Holdout Test Accuracy" : "CV Accuracy"}
                      value={formatMetric(results.metrics?.['Accuracy'], true)}
                    />
                    <StMetric
                      label={splitMethod === 'Train-Test Split' ? "Holdout Test Precision" : "CV Precision"}
                      value={formatMetric(results.metrics?.['Precision'], true)}
                    />
                    <StMetric
                      label={splitMethod === 'Train-Test Split' ? "Holdout Test Recall" : "CV Recall"}
                      value={formatMetric(results.metrics?.['Recall'], true)}
                    />
                    <StMetric
                      label={splitMethod === 'Train-Test Split' ? "Holdout Test F1" : "CV F1 Score"}
                      value={formatMetric(results.metrics?.['F1 Score'], true)}
                    />
                    {(results.metrics?.['OOB Score'] !== undefined || results.oob_score !== undefined) && (
                      <StMetric
                        label="Random Forest OOB Accuracy"
                        value={formatMetric(results.metrics?.['OOB Score'] ?? results.oob_score, true)}
                      />
                    )}
                  </>
                )}
              </div>

              {/* Add to Comparison Button */}
              <button
                type="button"
                onClick={handleAddToComparison}
                disabled={comparisonAdded}
                className="st-button-secondary w-full py-2 mt-2 text-xs"
              >
                {comparisonAdded ? 'Added to Comparison!' : 'Add Current Run to Comparison'}
              </button>

              <div className="st-divider my-5" />

              {/* Visualization Section */}
              <div>
                <h3 className="st-subheader">Visualization</h3>

                <StMultiselect
                  label="Select Plots"
                  options={availablePlotsList}
                  selected={selectedPlots}
                  onChange={(val) => setSelectedPlots(val)}
                />

                <StSelect
                  label="Plot Quality"
                  value={plotQuality}
                  onChange={(val) => setPlotQuality(val)}
                  options={[
                    'Screen Preview (150 DPI)',
                    'Publication (300 DPI)',
                    'High Quality (600 DPI)',
                    'Ultra Quality (1200 DPI)',
                  ]}
                />

                <StSelect
                  label="Figure Width"
                  value={figureWidth}
                  onChange={(val) => setFigureWidth(val)}
                  options={['Single Column (90 mm)', 'Double Column (190 mm)']}
                />

                <StSelect
                  label="Export Format"
                  value={exportFormat}
                  onChange={(val) => setExportFormat(val)}
                  options={['PNG', 'TIFF', 'PDF', 'SVG']}
                />

                <button
                  type="button"
                  onClick={() => setPlotsGenerated(true)}
                  className="st-button-secondary w-full py-2 mt-3 text-xs"
                >
                  Generate Plots
                </button>

                {/* Render Selected Generated Plots */}
                {plotsGenerated && (
                  <div className="space-y-6 mt-6">
                    {selectedPlots.map((plotName) => {
                      const imgUrl = api.getPlotUrl(results.job_id, plotName, plotQuality, exportFormat.toLowerCase());
                      return (
                        <div key={plotName} className="space-y-2">
                          <h4 className="text-sm font-semibold text-[var(--text-primary)]">{plotName}</h4>
                          <div
                            className="p-4 rounded-lg border flex justify-center items-center"
                            style={{
                              backgroundColor: 'var(--surface)',
                              borderColor: 'var(--border)',
                            }}
                          >
                            <img
                              src={imgUrl}
                              alt={plotName}
                              className="max-h-[480px] w-auto rounded object-contain"
                              loading="lazy"
                            />
                          </div>
                          <a
                            href={imgUrl}
                            download={`${plotName.toLowerCase().replace(/ /g, '_')}.${exportFormat.toLowerCase()}`}
                            className="st-button-secondary inline-flex items-center space-x-1.5 py-1.5 px-3 text-xs"
                          >
                            <Download className="h-3.5 w-3.5" />
                            <span>Download {plotName}</span>
                          </a>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="st-divider my-5" />

              {/* Export & Experiment Replication Section */}
              <div>
                <h3 className="st-subheader">📤 Export & Experiment Replication</h3>
                <p className="text-xs text-[var(--text-muted)] mb-3">
                  Export your results, predictions, standalone code, or a full reproducibility bundle for academic review.
                </p>

                <StTabs
                  tabs={['Python Script', 'Prediction CSV', 'PDF Report', 'Full Experiment ZIP']}
                  activeTab={exportTab}
                  onChange={(tab) => setExportTab(tab)}
                />

                <div className="mt-3">
                  {exportTab === 'Python Script' && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-bold text-[var(--text-primary)]">Standalone Python Script</h4>
                      <StAlert type="info">
                        Download a standalone Python script to reproduce this training run. The generated script includes data loading, preprocessing, model fitting, and plotting, having zero dependency on Solvosys.
                      </StAlert>
                      <a
                        href={api.getExportScriptUrl(results.job_id)}
                        download={`run_${results.model_name.toLowerCase().replace(/ /g, '_')}.py`}
                        className="st-button-primary inline-flex items-center space-x-2 py-2 px-4 text-xs"
                      >
                        <FileCode className="h-4 w-4" />
                        <span>Download Standalone Script (.py)</span>
                      </a>
                      <StExpander title="Preview Standalone Script">
                        <pre className="text-[11px] font-mono text-[var(--text-primary)] whitespace-pre overflow-x-auto p-2">
                          {scriptCode || 'Loading script...'}
                        </pre>
                      </StExpander>
                    </div>
                  )}

                  {exportTab === 'Prediction CSV' && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-bold text-[var(--text-primary)]">Prediction CSV</h4>
                      <StAlert type="info">
                        Download a CSV file containing the actual target values, model predictions, and residuals or probabilities on the test set.
                      </StAlert>
                      <a
                        href={api.getExportCsvUrl(results.job_id)}
                        download={`predictions_${results.model_name.toLowerCase().replace(/ /g, '_')}.csv`}
                        className="st-button-primary inline-flex items-center space-x-2 py-2 px-4 text-xs"
                      >
                        <FileSpreadsheet className="h-4 w-4" />
                        <span>Download Predictions CSV (.csv)</span>
                      </a>
                    </div>
                  )}

                  {exportTab === 'PDF Report' && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-bold text-[var(--text-primary)]">Academic PDF Report</h4>
                      <StAlert type="info">
                        Download an academic-quality publication report summarizing the dataset metadata, preprocessing steps, model hyperparameters, evaluation metrics, and embedded figures.
                      </StAlert>
                      <a
                        href={api.getExportPdfUrl(results.job_id)}
                        download={`report_${results.model_name.toLowerCase().replace(/ /g, '_')}.pdf`}
                        className="st-button-primary inline-flex items-center space-x-2 py-2 px-4 text-xs"
                      >
                        <FileText className="h-4 w-4" />
                        <span>Download PDF Research Report (.pdf)</span>
                      </a>
                    </div>
                  )}

                  {exportTab === 'Full Experiment ZIP' && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-bold text-[var(--text-primary)]">Experiment ZIP Bundle</h4>
                      <StAlert type="info">
                        Download a complete reproducibility bundle containing the standalone Python script, prediction CSV, PDF report, plots (if generated), README, and requirements.txt.
                      </StAlert>
                      <a
                        href={api.getExportZipUrl(results.job_id)}
                        download={`experiment_bundle_${results.model_name.toLowerCase().replace(/ /g, '_')}.zip`}
                        className="st-button-primary inline-flex items-center space-x-2 py-2 px-4 text-xs"
                      >
                        <Archive className="h-4 w-4" />
                        <span>Download Experiment Bundle (.zip)</span>
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
