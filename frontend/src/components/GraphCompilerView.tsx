import React, { useEffect, useState } from "react";
import { Play, Code, Zap, Download, RefreshCw, Cpu, BrainCircuit } from "lucide-react";
import { apiClient } from "../api/client";
import { ComputationalGraph } from "../types/index";
import { useAuth } from "../context/AuthContext";

export const GraphCompilerView: React.FC = () => {
  const { user } = useAuth();
  const [graphs, setGraphs] = useState<ComputationalGraph[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<ComputationalGraph | null>(null);
  const [_loading, setLoading] = useState<boolean>(false);
  const [compiling, setCompiling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form parameters
  const [name, setName] = useState<string>("Custom Fused Architecture");
  const [preset, setPreset] = useState<string>("mlp");
  const [backend, setBackend] = useState<string>("mps");
  const [selectedKernelIndex, setSelectedKernelIndex] = useState<number>(0);

  // Advisory state
  const [advisoryLoading, setAdvisoryLoading] = useState<boolean>(false);
  const [advisoryResult, setAdvisoryResult] = useState<string | null>(null);

  const loadGraphs = async () => {
    try {
      setLoading(true);
      const res = await apiClient.listGraphs(1, 10);
      setGraphs(res.items);
      if (res.items && res.items.length > 0) {
        setSelectedGraph(res.items[0]);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load graphs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraphs();
  }, []);

  const handleCompile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setError("Please log in as an operator to compile graphs");
      return;
    }
    try {
      setCompiling(true);
      setError(null);
      const newGraph = await apiClient.traceAndCompile(name, backend, preset);
      setGraphs([newGraph, ...graphs]);
      setSelectedGraph(newGraph);
      setSelectedKernelIndex(0);
      setAdvisoryResult(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Compilation failed");
    } finally {
      setCompiling(false);
    }
  };

  const handleRequestAdvice = async () => {
    if (!selectedGraph) return;
    try {
      setAdvisoryLoading(true);
      const advice = await apiClient.getAdvice(selectedGraph.target_backend, "fusion_and_memory", selectedGraph.id);
      setAdvisoryResult(`${advice.analysis}\n\nKey Actions:\n${advice.recommendations.map((r, i) => `${i + 1}. ${r}`).join("\n")}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Advisor request failed");
    } finally {
      setAdvisoryLoading(false);
    }
  };

  const exportSource = () => {
    if (!selectedGraph) return;
    const blob = new Blob(
      [selectedGraph.compiled_kernels.map((k) => `// ${k.name}\n${k.source_code}`).join("\n\n")],
      { type: "text/plain" }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedGraph.name.toLowerCase().replace(/\s+/g, "_")}_${selectedGraph.target_backend}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const activeKernel = selectedGraph?.compiled_kernels[selectedKernelIndex];

  return (
    <div className="space-y-6">
      {/* Configuration & Launch Panel */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
        <h2 className="text-lg font-semibold text-white flex items-center space-x-2 mb-4">
          <Zap className="w-5 h-5 text-amber-400" />
          <span>Inductor Graph Tracer & Kernel Compiler Studio</span>
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-950/60 border border-red-800 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleCompile} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Architecture Preset</label>
            <select
              value={preset}
              onChange={(e) => {
                setPreset(e.target.value);
                setName(`${e.target.value.toUpperCase()} Optimized Block`);
              }}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="mlp">MLP Projection Block</option>
              <option value="convnet">Vision ConvBlock</option>
              <option value="attention">Multi-Head Attention</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Target Accelerator</label>
            <select
              value={backend}
              onChange={(e) => setBackend(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="mps">Metal MSL (MPS 2.6+)</option>
              <option value="vulkan">Vulkan 1.3 GLSL</option>
              <option value="cuda">CUDA SM_90</option>
              <option value="cpu">Host CPU SIMD</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Model Graph Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={compiling}
              className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 px-4 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {compiling ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              <span>{compiling ? "Compiling..." : "Trace & Compile Passes"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Compiler Results & Metrics */}
      {selectedGraph && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-indigo-400" />
                  <span>Optimization Metrics</span>
                </h3>
                <span className="text-xs px-2 py-0.5 rounded bg-gray-800 border border-gray-700 uppercase font-mono text-indigo-300">
                  {selectedGraph.target_backend}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400">Kernel Count</div>
                  <div className="text-lg font-bold text-white mt-1">
                    {selectedGraph.metrics.fused_kernel_count}{" "}
                    <span className="text-xs text-gray-400 font-normal">(from {selectedGraph.metrics.original_op_count} ops)</span>
                  </div>
                  <div className="text-xs text-emerald-400 mt-0.5 font-medium">
                    {selectedGraph.metrics.reduction_ratio}x fusion reduction
                  </div>
                </div>

                <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400">Compiler Speedup</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">+{selectedGraph.metrics.speedup_percentage}%</div>
                  <div className="text-xs text-gray-400 mt-0.5">{selectedGraph.metrics.estimated_latency_ms} ms (fused)</div>
                </div>

                <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400">Total FLOPs</div>
                  <div className="text-lg font-bold text-white mt-1">{(selectedGraph.metrics.total_flops / 1e6).toFixed(1)} M</div>
                </div>

                <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-xs text-gray-400">Peak Memory Traffic</div>
                  <div className="text-lg font-bold text-white mt-1">{selectedGraph.metrics.peak_memory_mb} MB</div>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-gray-800">
                <button
                  onClick={exportSource}
                  className="w-full flex items-center justify-center space-x-2 bg-gray-800 hover:bg-gray-700 text-gray-200 py-1.5 px-3 rounded text-xs font-medium border border-gray-700"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export Generated Kernels</span>
                </button>

                <button
                  onClick={handleRequestAdvice}
                  disabled={advisoryLoading}
                  className="w-full flex items-center justify-center space-x-2 bg-indigo-900/40 hover:bg-indigo-900/60 text-indigo-300 py-1.5 px-3 rounded text-xs font-medium border border-indigo-700/50"
                >
                  <BrainCircuit className="w-3.5 h-3.5" />
                  <span>{advisoryLoading ? "Consulting..." : "Opt-in Advisory Diagnostics"}</span>
                </button>
              </div>

              {advisoryResult && (
                <div className="mt-4 p-3 bg-indigo-950/40 border border-indigo-800/60 rounded-lg text-xs text-indigo-200 whitespace-pre-line">
                  <div className="font-semibold text-indigo-300 mb-1">Advisory Diagnostic:</div>
                  {advisoryResult}
                </div>
              )}
            </div>

            {/* Past Compiled Graphs History */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                Recent Compilations
              </h4>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {graphs.map((g) => (
                  <button
                    key={g.id}
                    onClick={() => {
                      setSelectedGraph(g);
                      setSelectedKernelIndex(0);
                    }}
                    className={`w-full text-left p-2 rounded text-xs transition-colors flex items-center justify-between ${
                      selectedGraph.id === g.id
                        ? "bg-indigo-900/40 border border-indigo-700 text-white"
                        : "text-gray-300 hover:bg-gray-800"
                    }`}
                  >
                    <span className="font-medium truncate">{g.name}</span>
                    <span className="text-[10px] uppercase font-mono px-1 py-0.5 rounded bg-gray-800 text-gray-400 ml-2">
                      {g.target_backend}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column (2 spans): Generated Kernel Source Viewer */}
          <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Code className="w-4 h-4 text-emerald-400" />
                <h3 className="font-semibold text-white">Generated Kernel Source</h3>
              </div>
              <div className="flex space-x-1">
                {selectedGraph.compiled_kernels.map((k, idx) => (
                  <button
                    key={k.kernel_id}
                    onClick={() => setSelectedKernelIndex(idx)}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      selectedKernelIndex === idx
                        ? "bg-indigo-600 text-white"
                        : "bg-gray-800 text-gray-400 hover:text-white"
                    }`}
                  >
                    Kernel #{idx + 1}
                  </button>
                ))}
              </div>
            </div>

            {activeKernel && (
              <div className="flex-1 flex flex-col">
                <div className="bg-gray-950 p-2.5 rounded-t-lg border-b border-gray-800 text-xs text-gray-400 flex items-center justify-between font-mono">
                  <span>{activeKernel.name}</span>
                  <span className="text-indigo-400">Fused: [{activeKernel.fused_ops.join(" + ")}]</span>
                </div>
                <pre className="flex-1 bg-gray-950 p-4 rounded-b-lg text-emerald-400 font-mono text-xs overflow-x-auto leading-relaxed border border-gray-800 border-t-0">
                  <code>{activeKernel.source_code}</code>
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
