import React, { createContext, useContext, useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { OIDCConfig, UserProfile } from "../types/index";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  oidcConfig: OIDCConfig | null;
  isLoading: boolean;
  error: string | null;
  loginDemo: (username?: string, role?: string) => Promise<void>;
  loginOIDC: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function generateRandomString(length: number): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
  const values = new Uint8Array(length);
  crypto.getRandomValues(values);
  return Array.from(values, (v) => chars[v % chars.length]).join("");
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const data = new TextEncoder().encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  const bin = String.fromCharCode(...new Uint8Array(digest));
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [oidcConfig, setOidcConfig] = useState<OIDCConfig | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function initAuth() {
      try {
        const config = await apiClient.getOIDCConfig();
        setOidcConfig(config);

        // Check if returning from OIDC redirect callback
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get("code");
        const state = urlParams.get("state");

        if (code && state) {
          const storedState = sessionStorage.getItem("pkce_state");
          const codeVerifier = sessionStorage.getItem("pkce_verifier");

          if (storedState !== state || !codeVerifier) {
            throw new Error("Invalid PKCE state verification or missing verifier");
          }

          // Clean up temporary sessionStorage PKCE artifacts
          sessionStorage.removeItem("pkce_state");
          sessionStorage.removeItem("pkce_verifier");

          const redirectUri = window.location.origin + window.location.pathname;
          const tokenResp = await apiClient.exchangeToken(code, codeVerifier, redirectUri);

          // Access token is kept strictly in-memory (never written to localStorage)
          setToken(tokenResp.access_token);
          apiClient.setToken(tokenResp.access_token);
          setUser(tokenResp.user);

          // Clean URL params
          window.history.replaceState({}, document.title, window.location.pathname);
        } else if (config.demo_mode_enabled && !token) {
          // Default convenient bootstrap in local demo environment
          const demoResp = await apiClient.demoLogin("alan_engineer", "operator");
          setToken(demoResp.access_token);
          apiClient.setToken(demoResp.access_token);
          setUser(demoResp.user);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Authentication initialization failed");
      } finally {
        setIsLoading(false);
      }
    }

    initAuth();
  }, []);

  const loginDemo = async (username = "alan_engineer", role = "operator") => {
    try {
      setIsLoading(true);
      setError(null);
      const resp = await apiClient.demoLogin(username, role);
      setToken(resp.access_token);
      apiClient.setToken(resp.access_token);
      setUser(resp.user);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Demo login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const loginOIDC = async () => {
    if (!oidcConfig) return;
    try {
      const verifier = generateRandomString(64);
      const challenge = await generateCodeChallenge(verifier);
      const state = generateRandomString(32);

      // Store temporary PKCE verifier in sessionStorage across browser redirect
      sessionStorage.setItem("pkce_verifier", verifier);
      sessionStorage.setItem("pkce_state", state);

      const redirectUri = encodeURIComponent(window.location.origin + window.location.pathname);
      const authUrl = `${oidcConfig.issuer}/protocol/openid-connect/auth?client_id=${encodeURIComponent(
        oidcConfig.client_id
      )}&response_type=code&scope=openid%20profile%20email&redirect_uri=${redirectUri}&code_challenge=${encodeURIComponent(
        challenge
      )}&code_challenge_method=S256&state=${encodeURIComponent(state)}`;

      window.location.href = authUrl;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate OIDC login");
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    apiClient.setToken(null);
    sessionStorage.removeItem("pkce_verifier");
    sessionStorage.removeItem("pkce_state");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        oidcConfig,
        isLoading,
        error,
        loginDemo,
        loginOIDC,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
