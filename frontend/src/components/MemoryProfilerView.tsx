import React, { useEffect, useState } from "react";
import { HardDrive, Activity, CheckCircle2, AlertOctagon } from "lucide-react";
import { apiClient } from "../api/client";
import { ProfilerRun } from "../types/index";
import { useAuth } from "../context/AuthContext";

export const MemoryProfilerView: React.FC = () => {
  const { user } = useAuth();
  const [runs, setRuns] = useState<ProfilerRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<ProfilerRun | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Simulation controls
  const [sampleCount, setSampleCount] = useState<number>(50000);
  const [workerCount, setWorkerCount] = useState<number>(4);
  const [batchSize] = useState<number>(128);
  const [ipcMode, setIpcMode] = useState<string>("fork_python_list");

  const loadRuns = async () => {
    try {
      const data = await apiClient.listProfilerRuns();
      setRuns(data);
      if (data.length > 0 && !selectedRun) {
        setSelectedRun(data[0]);
      }
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setError("Please log in as an operator to run simulations");
      return;
    }
    try {
      setSimulating(true);
      setError(null);
      const newRun = await apiClient.runProfiler(sampleCount, workerCount, batchSize, ipcMode);
      setRuns([newRun, ...runs]);
      setSelectedRun(newRun);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Simulation Configuration */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
        <h2 className="text-lg font-semibold text-white flex items-center space-x-2 mb-2">
          <HardDrive className="w-5 h-5 text-indigo-400" />
          <span>DataLoader Multi-Worker Memory Replication Profiler</span>
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          Diagnoses Linux copy-on-write page dirtying & memory amplification across worker pools (PyTorch Issue #13246)
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-950/60 border border-red-800 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSimulate} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">IPC Buffer Regime</label>
            <select
              value={ipcMode}
              onChange={(e) => setIpcMode(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none"
            >
              <option value="fork_python_list">Fork + Python List</option>
              <option value="fork_numpy_array">Fork + NumPy Array</option>
              <option value="spawn_shared_ipc">Spawn + POSIX Shared Memory</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Worker Count (num_workers)</label>
            <select
              value={workerCount}
              onChange={(e) => setWorkerCount(Number(e.target.value))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none"
            >
              {[0, 2, 4, 8, 16].map((w) => <option key={w} value={w}>{w === 0 ? "0 (Single Process GIL)" : `${w} Workers`}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Dataset Samples</label>
            <select
              value={sampleCount}
              onChange={(e) => setSampleCount(Number(e.target.value))}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none"
            >
              {[20000, 50000, 100000].map((s) => <option key={s} value={s}>{s.toLocaleString()} samples</option>)}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={simulating}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 px-3 rounded-lg text-xs transition-colors"
            >
              {simulating ? "Profiling..." : "Run Memory Simulation"}
            </button>
          </div>
        </form>
      </div>

      {/* Profiler Results */}
      {selectedRun && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Key Metrics Cards (2 cols) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <span>Memory Allocation Profile</span>
                </h3>
                <span className="text-xs px-2 py-0.5 rounded bg-gray-800 border border-gray-700 font-mono text-gray-300">
                  Mode: {selectedRun.ipc_mode}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400">Total Memory Footprint</div>
                  <div className="text-xl font-bold text-white mt-1">
                    {selectedRun.total_memory_mb} MB
                  </div>
                  <div className="text-[11px] text-gray-400 mt-0.5">
                    Parent: {selectedRun.parent_memory_mb} MB | Workers: {selectedRun.worker_memory_mb} MB
                  </div>
                </div>

                <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400">Memory Amplification</div>
                  <div
                    className={`text-xl font-bold mt-1 ${
                      selectedRun.amplification_ratio > 1.5 ? "text-rose-400" : "text-emerald-400"
                    }`}
                  >
                    {selectedRun.amplification_ratio}x
                  </div>
                  <div className="text-[11px] text-gray-400 mt-0.5">
                    {selectedRun.amplification_ratio > 1.5 ? "COW Duplication Active" : "Zero-Copy Compliant"}
                  </div>
                </div>

                <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400">Throughput</div>
                  <div className="text-xl font-bold text-white mt-1">
                    {selectedRun.throughput_samples_sec}
                  </div>
                  <div className="text-[11px] text-gray-400 mt-0.5">samples / sec</div>
                </div>
              </div>

              {/* Status Banner */}
              <div
                className={`p-3 rounded-lg border text-xs flex items-center space-x-2 ${
                  selectedRun.zero_copy_verified
                    ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
                    : "bg-rose-950/40 border-rose-800/60 text-rose-300"
                }`}
              >
                {selectedRun.zero_copy_verified ? (
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                ) : (
                  <AlertOctagon className="w-4 h-4 flex-shrink-0" />
                )}
                <span>{selectedRun.notes}</span>
              </div>
            </div>
          </div>

          {/* Past Runs History (1 col) */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              Simulation Benchmarks
            </h4>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {runs.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedRun(r)}
                  className={`w-full text-left p-2.5 rounded text-xs transition-colors flex items-center justify-between ${
                    selectedRun.id === r.id
                      ? "bg-indigo-900/40 border border-indigo-700 text-white"
                      : "text-gray-300 hover:bg-gray-800"
                  }`}
                >
                  <div>
                    <div className="font-medium">{r.title}</div>
                    <div className="text-[10px] text-gray-400 font-mono mt-0.5">
                      {r.worker_count} workers | {r.total_memory_mb} MB
                    </div>
                  </div>
                  <span
                    className={`font-mono text-xs font-bold ${
                      r.amplification_ratio > 1.5 ? "text-rose-400" : "text-emerald-400"
                    }`}
                  >
                    {r.amplification_ratio}x
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
