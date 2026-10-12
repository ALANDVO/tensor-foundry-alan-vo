import React, { useEffect, useState } from "react";
import { Search, CheckCircle2, Clock, AlertTriangle, XCircle, ShieldAlert } from "lucide-react";
import { apiClient } from "../api/client";
import { LowerabilityResponse, OpCatalogItem, TriageRankingItem } from "../types/index";

export const CoverageMatrixView: React.FC = () => {
  const [items, setItems] = useState<OpCatalogItem[]>([]);
  const [triage, setTriage] = useState<TriageRankingItem[]>([]);
  const [_loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>("");
  const [category, setCategory] = useState<string>("");
  const [targetBackend, setTargetBackend] = useState<string>("mps");

  // Lowerability Analyzer State
  const [lowerability, setLowerability] = useState<LowerabilityResponse | null>(null);
  const [customOpsInput, setCustomOpsInput] = useState<string>("matmul, relu, grid_sampler_3d, linalg_qr");
  const [analyzing, setAnalyzing] = useState<boolean>(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [matrixData, triageData] = await Promise.all([
        apiClient.getCoverageMatrix(category || undefined, search || undefined, undefined, targetBackend),
        apiClient.getTriageRankings()
      ]);
      setItems(matrixData);
      setTriage(triageData);
    } catch {
      // Error handling
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [category, targetBackend]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchData();
  };

  const runLowerabilityAnalysis = async () => {
    try {
      setAnalyzing(true);
      const ops = customOpsInput
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const res = await apiClient.analyzeGraphLowerability(targetBackend, undefined, ops);
      setLowerability(res);
    } catch {
      // Handle error
    } finally {
      setAnalyzing(false);
    }
  };

  const renderStatusBadge = (status: string) => {
    const config = {
      supported: { cls: "bg-emerald-950 text-emerald-400 border-emerald-800", icon: CheckCircle2, text: "Supported" },
      in_progress: { cls: "bg-amber-950 text-amber-400 border-amber-800", icon: Clock, text: "Nightly" },
      planned: { cls: "bg-blue-950 text-blue-400 border-blue-800", icon: AlertTriangle, text: "Planned" }
    }[status] || { cls: "bg-rose-950 text-rose-400 border-rose-800", icon: XCircle, text: "Missing" };
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs border ${config.cls}`}>
        <Icon className="w-3 h-3" />
        <span>{config.text}</span>
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Lowerability Analyzer Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
        <h2 className="text-lg font-semibold text-white flex items-center space-x-2 mb-2">
          <ShieldAlert className="w-5 h-5 text-indigo-400" />
          <span>Graph Lowerability & Fallback Analyzer</span>
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          Evaluates arbitrary model operator sets against accelerator backends (PyTorch Issues #77764, #141287, #160230)
        </p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-400 mb-1">Operator Set (comma-separated)</label>
            <input
              type="text"
              value={customOpsInput}
              onChange={(e) => setCustomOpsInput(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs font-mono text-gray-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Target Accelerator</label>
            <select
              value={targetBackend}
              onChange={(e) => setTargetBackend(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
            >
              {["mps", "vulkan", "cuda", "cpu"].map((b) => <option key={b} value={b}>{b.toUpperCase()}</option>)}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={runLowerabilityAnalysis}
              disabled={analyzing}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 px-3 rounded-lg text-xs transition-colors"
            >
              {analyzing ? "Analyzing..." : "Analyze Lowerability"}
            </button>
          </div>
        </div>

        {lowerability && (
          <div className="mt-4 p-4 bg-gray-800/60 border border-gray-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-white">
                Lowerability Score:{" "}
                <span className={lowerability.lowerability_percentage >= 80 ? "text-emerald-400" : "text-amber-400"}>
                  {lowerability.lowerability_percentage}%
                </span>
              </span>
              <span className="text-xs text-gray-400">
                Fallback host transfers required:{" "}
                <strong className="text-rose-400">{lowerability.fallback_transfers_required}</strong>
              </span>
            </div>
            <ul className="text-xs text-gray-300 space-y-1 list-disc list-inside">
              {lowerability.diagnostic_recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Operator Matrix & Triage Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Matrix Table (2 cols) */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
            <h3 className="font-semibold text-white">Operator Coverage Matrix</h3>

            <div className="flex space-x-2 w-full sm:w-auto">
              <form onSubmit={handleSearchSubmit} className="relative flex-1 sm:w-48">
                <input
                  type="text"
                  placeholder="Search op..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-gray-200 focus:outline-none"
                />
                <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" />
              </form>

              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-300 focus:outline-none"
              >
                {["", "linalg", "vision_3d", "activation", "indexing"].map((c) => <option key={c} value={c}>{c || "All Categories"}</option>)}
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-800/60 text-gray-400 border-b border-gray-800">
                <tr>{["Operator Name", "Category", "CPU", "CUDA", "Apple MPS", "Vulkan"].map((h) => <th key={h} className="p-3">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-800/40">
                    <td className="p-3 font-mono font-medium text-white">{item.op_name}</td>
                    <td className="p-3 text-gray-400">{item.category}</td>
                    {[item.cpu_status, item.cuda_status, item.mps_status, item.vulkan_status].map((s, idx) => (
                      <td key={idx} className="p-3">{renderStatusBadge(s)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Triage Priority Queue (1 col) */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
          <h3 className="font-semibold text-white mb-2">Community Triage Backlog</h3>
          <p className="text-xs text-gray-400 mb-4">Ranked by requests and multi-hardware gap score</p>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {triage.map((t, idx) => (
              <div key={t.op_name} className="p-3 bg-gray-800/50 border border-gray-700/60 rounded-lg text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono font-bold text-white">#{idx + 1} {t.op_name}</span>
                  <span className="px-1.5 py-0.5 rounded bg-indigo-900/60 text-indigo-300 font-mono text-[10px]">
                    Score: {t.priority_score}
                  </span>
                </div>
                <div className="text-gray-400 text-[11px] font-mono truncate">{t.pytorch_symbol}</div>
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-700/40 text-[11px]">
                  <span className="text-gray-400">{t.request_count} GitHub requests</span>
                  <span className="text-rose-400 font-mono">Missing: {t.missing_targets.join(", ")}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
