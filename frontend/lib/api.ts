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

export type Analysis = {
  summary: string;
  tags: string[] | null;
  category: string | null;
  score: number;
  score_reason: string | null;
  model: string | null;
  analyzed_at: string;
};

export type Article = {
  id: number;
  source_id: number;
  url: string;
  title: string;
  author: string | null;
  published_at: string | null;
  summary: string | null;
  lang: string | null;
  collected_at: string;
  analysis: Analysis | null;
};

export type ArticleListResponse = {
  items: Article[];
  total: number;
  limit: number;
  offset: number;
};

export type Source = {
  id: number;
  name: string;
  type: string;
  url: string;
  description: string | null;
  enabled: boolean;
  last_fetched_at: string | null;
  last_status: string | null;
  last_error: string | null;
};

export type UserAction = {
  id: number;
  article_id: number;
  action: string;
  note: string | null;
  channel: string;
  created_at: string;
};

export const ACTION_LABELS: Record<string, string> = {
  bookmark: "收藏",
  later: "稍后读",
  dismiss: "不感兴趣",
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
  const { data, headers } = await api.get<Article[] | ArticleListResponse>("/articles", { params });
  if (Array.isArray(data)) {
    const total = Number(headers["x-total-count"] ?? data.length);
    const limit = Number(params.limit ?? 20);
    const offset = Number(params.offset ?? 0);
    return { items: data, total, limit, offset };
  }
  return data as ArticleListResponse;
}

export async function fetchSources() {
  const { data } = await api.get<Source[]>("/sources");
  return data;
}

export async function updateSource(sourceId: number, payload: { enabled?: boolean; name?: string; description?: string }) {
  const { data } = await api.patch<Source>(`/sources/${sourceId}`, payload);
  return data;
}

export async function fetchPushLogs(params: Record<string, string | number | undefined> = {}) {
  const { data } = await api.get<PushLog[]>("/push-logs", { params });
  return data;
}

export async function fetchUserActions(params: Record<string, string | number | undefined> = {}) {
  const { data } = await api.get<UserAction[]>("/user-actions", { params });
  return data;
}

export async function postUserAction(article_id: number, action: string, note?: string) {
  const { data } = await api.post("/user-actions", { article_id, action, note, channel: "dashboard" });
  return data;
}
