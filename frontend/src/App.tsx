import React, { useState } from "react";
import { AuthProvider } from "./context/AuthContext";
import { Header } from "./components/Header";
import { GraphCompilerView } from "./components/GraphCompilerView";
import { CoverageMatrixView } from "./components/CoverageMatrixView";
import { MemoryProfilerView } from "./components/MemoryProfilerView";
import { AuditLogView } from "./components/AuditLogView";

export const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("compiler");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col font-sans">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "compiler" && <GraphCompilerView />}
        {activeTab === "coverage" && <CoverageMatrixView />}
        {activeTab === "profiler" && <MemoryProfilerView />}
        {activeTab === "audit" && <AuditLogView />}
      </main>

      <footer className="border-t border-gray-900 bg-gray-950 py-4 text-center text-xs text-gray-500">
        <p>
          TensorFoundry &copy; 2026 Alan Vo (
          <a href="mailto:alanvo@gmail.com" className="text-indigo-400 hover:underline">
            alanvo@gmail.com
          </a>
          ). High-performance tensor execution and compiler simulator.
        </p>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
