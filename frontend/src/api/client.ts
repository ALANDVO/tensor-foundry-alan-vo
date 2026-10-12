import {
  AuditLogItem,
  ComputationalGraph,
  LowerabilityResponse,
  OIDCConfig,
  OpCatalogItem,
  PageResponse,
  ProfilerRun,
  TokenResponse,
  TriageRankingItem,
  UserProfile
} from "../types/index";

const API_BASE = (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_BASE_URL) || "";

export class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> || {})
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers
    });

    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) errorMsg = errorJson.detail;
      } catch {
        // Fallback to status text
      }
      throw new Error(errorMsg);
    }

    if (res.status === 204) {
      return {} as T;
    }

    return res.json() as Promise<T>;
  }

  // Auth endpoints
  async getOIDCConfig(): Promise<OIDCConfig> {
    return this.request<OIDCConfig>("/api/v1/auth/config");
  }

  async demoLogin(username: string, requestedRole: string): Promise<TokenResponse> {
    return this.request<TokenResponse>("/api/v1/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({ username, requested_role: requestedRole })
    });
  }

  async exchangeToken(code: string, codeVerifier: string, redirectUri: string): Promise<TokenResponse> {
    return this.request<TokenResponse>("/api/v1/auth/token", {
      method: "POST",
      body: JSON.stringify({
        grant_type: "authorization_code",
        code,
        code_verifier: codeVerifier,
        redirect_uri: redirectUri
      })
    });
  }

  async getMe(): Promise<UserProfile> {
    return this.request<UserProfile>("/api/v1/auth/me");
  }

  // Compiler endpoints
  async listGraphs(page = 1, pageSize = 10, targetBackend?: string): Promise<PageResponse<ComputationalGraph>> {
    const query = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (targetBackend) query.set("target_backend", targetBackend);
    return this.request<PageResponse<ComputationalGraph>>(`/api/v1/compiler/graphs?${query.toString()}`);
  }

  async traceAndCompile(name: string, targetBackend: string, preset: string, description?: string): Promise<ComputationalGraph> {
    return this.request<ComputationalGraph>("/api/v1/compiler/trace", {
      method: "POST",
      body: JSON.stringify({ name, target_backend: targetBackend, architecture_preset: preset, description })
    });
  }

  async getGraph(graphId: string): Promise<ComputationalGraph> {
    return this.request<ComputationalGraph>(`/api/v1/compiler/graphs/${graphId}`);
  }

  async deleteGraph(graphId: string): Promise<void> {
    return this.request<void>(`/api/v1/compiler/graphs/${graphId}`, { method: "DELETE" });
  }

  // Coverage endpoints
  async getCoverageMatrix(category?: string, search?: string, targetStatus?: string, targetBackend = "mps"): Promise<OpCatalogItem[]> {
    const query = new URLSearchParams({ target_backend: targetBackend });
    if (category) query.set("category", category);
    if (search) query.set("search", search);
    if (targetStatus) query.set("target_status", targetStatus);
    return this.request<OpCatalogItem[]>(`/api/v1/coverage/matrix?${query.toString()}`);
  }

  async analyzeGraphLowerability(targetBackend: string, graphId?: string, operatorList?: string[]): Promise<LowerabilityResponse> {
    return this.request<LowerabilityResponse>("/api/v1/coverage/analyze-graph", {
      method: "POST",
      body: JSON.stringify({
        target_backend: targetBackend,
        graph_id: graphId,
        operator_list: operatorList
      })
    });
  }

  async getTriageRankings(): Promise<TriageRankingItem[]> {
    return this.request<TriageRankingItem[]>("/api/v1/coverage/triage");
  }

  // Profiler endpoints
  async runProfiler(sampleCount: number, workerCount: number, batchSize: number, ipcMode: string): Promise<ProfilerRun> {
    return this.request<ProfilerRun>("/api/v1/profiler/simulate", {
      method: "POST",
      body: JSON.stringify({
        title: `Run: ${workerCount} workers (${ipcMode})`,
        sample_count: sampleCount,
        worker_count: workerCount,
        batch_size: batchSize,
        ipc_mode: ipcMode
      })
    });
  }

  async listProfilerRuns(): Promise<ProfilerRun[]> {
    return this.request<ProfilerRun[]>("/api/v1/profiler/runs");
  }

  // Advisor endpoints
  async getAdvice(targetBackend: string, focusArea: string, graphId?: string) {
    return this.request<{ analysis: string; recommendations: string[]; [k: string]: any }>("/api/v1/advisor/recommend", {
      method: "POST",
      body: JSON.stringify({ target_backend: targetBackend, focus_area: focusArea, graph_id: graphId })
    });
  }

  // Audit endpoints
  async getAuditLogs(limit = 50): Promise<AuditLogItem[]> {
    return this.request<AuditLogItem[]>(`/api/v1/audit/logs?limit=${limit}`);
  }
}

export const apiClient = new ApiClient();
