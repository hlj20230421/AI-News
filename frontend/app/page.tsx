"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchStats } from "../lib/api";

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });

  if (isLoading) return <p>加载中...</p>;
  if (error) return <p className="error">加载统计失败</p>;

  const stats = [
    { label: "信息源", value: data?.sources_total ?? 0 },
    { label: "启用源", value: data?.sources_enabled ?? 0 },
    { label: "文章总数", value: data?.articles_total ?? 0 },
    { label: "近 24h 文章", value: data?.articles_today ?? 0 },
    { label: "已分析", value: data?.analyses_total ?? 0 },
    { label: "LLM 成本 ($)", value: (data?.cost_usd_total ?? 0).toFixed(2) },
    { label: "近 24h 推送", value: data?.pushes_today ?? 0 },
  ];

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="grid">
        {stats.map((item) => (
          <div key={item.label} className="stat">
            <div className="label">{item.label}</div>
            <div className="value">{item.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
