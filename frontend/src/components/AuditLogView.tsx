import React, { useEffect, useState } from "react";
import { ClipboardList, RefreshCw } from "lucide-react";
import { apiClient } from "../api/client";
import { AuditLogItem } from "../types/index";
import { useAuth } from "../context/AuthContext";

export const AuditLogView: React.FC = () => {
  const { user } = useAuth();
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.getAuditLogs(50);
      setLogs(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.roles.includes("admin")) {
      fetchLogs();
    } else {
      setLoading(false);
    }
  }, [user]);

  if (!user?.roles.includes("admin")) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
        <ClipboardList className="w-10 h-10 text-gray-600 mx-auto mb-3" />
        <h3 className="text-white font-medium mb-1">Administrative Privileges Required</h3>
        <p className="text-xs text-gray-400">
          Audit logs are restricted to accounts with the <code className="text-indigo-400">admin</code> role.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white flex items-center space-x-2">
          <ClipboardList className="w-5 h-5 text-indigo-400" />
          <span>System Security & Mutation Audit Logs</span>
        </h2>
        <button
          onClick={fetchLogs}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-950/60 border border-red-800 rounded-lg text-red-300 text-xs">
          {error}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-gray-800/60 text-gray-400 border-b border-gray-800">
            <tr>{["Timestamp (UTC)", "User", "Role", "Action", "Resource", "Status"].map((h) => <th key={h} className="p-3">{h}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-800/40">
                <td className="p-3 font-mono text-gray-400">
                  {new Date(log.timestamp).toISOString().replace("T", " ").substring(0, 19)}
                </td>
                <td className="p-3 text-white font-medium">{log.user_email}</td>
                <td className="p-3">
                  <span className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-700 font-mono text-[10px]">
                    {log.user_role}
                  </span>
                </td>
                <td className="p-3 font-mono text-indigo-300 font-semibold">{log.action}</td>
                <td className="p-3 text-gray-400 font-mono">{log.resource_type} / {log.resource_id}</td>
                <td className="p-3">
                  <span className="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px]">
                    {log.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
