import React from "react";
import { Cpu, ShieldCheck, UserCheck, LogOut, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  const { user, oidcConfig, loginDemo, loginOIDC, logout } = useAuth();

  const tabs = [
    { id: "compiler", label: "Graph & Compiler" },
    { id: "coverage", label: "Op Coverage Matrix" },
    { id: "profiler", label: "DataLoader Profiler" },
    { id: "audit", label: "Audit Logs" }
  ];

  return (
    <header className="border-b border-gray-800 bg-gray-900/90 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-600 rounded-lg shadow">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold text-white tracking-tight">TensorFoundry</span>
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-900/60 text-indigo-300 border border-indigo-700/50">
                  Alan Vo
                </span>
              </div>
              <p className="text-xs text-gray-400">Dynamic Neural Graph & Multi-Backend Compiler</p>
            </div>
          </div>

          <nav className="flex space-x-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-gray-800 text-indigo-400 border-b-2 border-indigo-500"
                    : "text-gray-300 hover:bg-gray-800/60 hover:text-white"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          <div className="flex items-center space-x-3">
            {user ? (
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-200 flex items-center justify-end space-x-1">
                    <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{user.name}</span>
                  </div>
                  <div className="text-xs text-gray-400 flex items-center space-x-1">
                    <span className="px-1.5 py-0.2 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded font-mono">
                      {user.roles.join(", ")}
                    </span>
                    {user.is_demo_user && <span className="text-amber-400 font-semibold">[DEMO]</span>}
                  </div>
                </div>
                <button onClick={logout} title="Logout" className="p-1.5 rounded-md text-gray-400 hover:text-red-400 hover:bg-gray-800">
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                {oidcConfig?.demo_mode_enabled && (
                  <button
                    onClick={() => loginDemo("alan_engineer", "operator")}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded bg-emerald-600/20 text-emerald-300 border border-emerald-500/50 hover:bg-emerald-600/30 text-xs font-medium"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Demo Operator</span>
                  </button>
                )}
                <button
                  onClick={loginOIDC}
                  className="flex items-center space-x-1 px-3 py-1.5 rounded bg-indigo-600 text-white hover:bg-indigo-500 text-xs font-medium"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Keycloak OIDC</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
