"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchSources } from "../../lib/api";

export default function SourcesPage() {
  const { data = [], isLoading, error } = useQuery({
    queryKey: ["sources"],
    queryFn: fetchSources,
  });

  if (isLoading) return <p>加载中...</p>;
  if (error) return <p className="error">加载信息源失败</p>;

  return (
    <div>
      <h2>信息源</h2>
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>类型</th>
              <th>状态</th>
              <th>最近抓取</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row: any) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.name}</td>
                <td>{row.type}</td>
                <td>{row.enabled ? "启用" : "停用"}</td>
                <td>
                  {row.last_fetched_at
                    ? new Date(row.last_fetched_at).toLocaleString()
                    : "-"}
                  {row.last_status ? ` (${row.last_status})` : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!data.length ? <p className="muted">暂无信息源，请运行 seed_sources</p> : null}
      </div>
    </div>
  );
}
