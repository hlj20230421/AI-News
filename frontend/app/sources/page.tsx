"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchSources, Source, updateSource } from "../../lib/api";

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN");
}

function statusBadge(status: string | null) {
  if (!status) return null;
  const normalized = status.toLowerCase();
  let cls = "status-badge";
  if (normalized.includes("ok") || normalized.includes("success")) cls += " status-ok";
  else if (normalized.includes("fail") || normalized.includes("error")) cls += " status-error";
  else cls += " status-neutral";
  return <span className={cls}>{status}</span>;
}

function SourceToggle({
  source,
  onToggle,
  disabled,
}: {
  source: Source;
  onToggle: (id: number, enabled: boolean) => void;
  disabled: boolean;
}) {
  return (
    <label className="toggle" title={source.enabled ? "点击停用" : "点击启用"}>
      <input
        type="checkbox"
        checked={source.enabled}
        disabled={disabled}
        onChange={(e) => onToggle(source.id, e.target.checked)}
      />
      <span className="toggle-slider" />
      <span className="toggle-label">{source.enabled ? "启用" : "停用"}</span>
    </label>
  );
}

export default function SourcesPage() {
  const queryClient = useQueryClient();
  const { data = [], isLoading, error } = useQuery({
    queryKey: ["sources"],
    queryFn: fetchSources,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      updateSource(id, { enabled }),
    onMutate: async ({ id, enabled }) => {
      await queryClient.cancelQueries({ queryKey: ["sources"] });
      const previous = queryClient.getQueryData<Source[]>(["sources"]);
      queryClient.setQueryData<Source[]>(["sources"], (old) =>
        old?.map((s) => (s.id === id ? { ...s, enabled } : s))
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["sources"], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  function handleToggle(id: number, enabled: boolean) {
    toggleMutation.mutate({ id, enabled });
  }

  if (isLoading) return <div className="empty-state card">加载中…</div>;
  if (error) return <p className="error">加载信息源失败</p>;

  const enabledCount = data.filter((s) => s.enabled).length;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>信息源</h2>
          <p className="page-desc">
            共 {data.length} 个源，{enabledCount} 个启用 — 可通过开关控制是否参与采集
          </p>
        </div>
      </div>

      <div className="card source-table-wrap">
        <table className="table source-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>类型</th>
              <th>状态</th>
              <th>启用</th>
              <th>最近抓取</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.id} className={row.enabled ? "" : "row-disabled"}>
                <td>
                  <div className="source-name">{row.name}</div>
                  <div className="source-url muted">{row.url}</div>
                  {row.description ? (
                    <div className="source-desc muted">{row.description}</div>
                  ) : null}
                </td>
                <td>
                  <span className="type-chip">{row.type}</span>
                </td>
                <td>
                  <span className={`enabled-pill ${row.enabled ? "on" : "off"}`}>
                    {row.enabled ? "运行中" : "已停用"}
                  </span>
                </td>
                <td>
                  <SourceToggle
                    source={row}
                    onToggle={handleToggle}
                    disabled={toggleMutation.isPending}
                  />
                </td>
                <td>
                  <div>{formatDate(row.last_fetched_at)}</div>
                  {statusBadge(row.last_status)}
                  {row.last_error ? (
                    <div className="error source-error">{row.last_error}</div>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!data.length ? (
          <p className="muted empty-inline">暂无信息源，请运行 seed_sources</p>
        ) : null}
      </div>
    </div>
  );
}
