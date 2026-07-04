import axios from "axios";
import { clearToken, getToken } from "./auth";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE || "/api",
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      clearToken();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export type Stats = {
  sources_total: number;
  sources_enabled: number;
  articles_total: number;
  articles_today: number;
  analyses_total: number;
  cost_usd_total: number;
  pushes_today: number;
};

export type PushLog = {
  id: number;
  channel: string;
  event: string;
  batch_key: string;
  article_id: number | null;
  status: string;
  error: string | null;
  pushed_at: string;
};

export async function login(password: string) {
  const { data } = await api.post<{ access_token: string; expires_in: number }>("/auth/login", { password });
  return data;
}

export async function fetchStats() {
  const { data } = await api.get<Stats>("/stats");
  return data;
}

export async function fetchArticles(params: Record<string, string | number | undefined> = {}) {
  const { data } = await api.get("/articles", { params });
  return data as any[];
}

export async function fetchSources() {
  const { data } = await api.get("/sources");
  return data as any[];
}

export async function fetchPushLogs(params: Record<string, string | number | undefined> = {}) {
  const { data } = await api.get<PushLog[]>("/push-logs", { params });
  return data;
}

export async function postUserAction(article_id: number, action: string, note?: string) {
  const { data } = await api.post("/user-actions", { article_id, action, note, channel: "dashboard" });
  return data;
}
