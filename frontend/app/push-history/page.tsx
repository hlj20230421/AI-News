"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchPushLogs } from "../../lib/api";

export default function PushHistoryPage() {
  const [event, setEvent] = useState("");
  const [status, setStatus] = useState("");

  const { data = [], refetch, isFetching } = useQuery({
    queryKey: ["push-logs", event, status],
    queryFn: () =>
      fetchPushLogs({
        event: event || undefined,
        status: status || undefined,
        limit: 100,
      }),
  });

  return (
    <div>
      <h2>推送历史</h2>
      <div className="toolbar">
        <select value={event} onChange={(e) => setEvent(e.target.value)}>
          <option value="">全部事件</option>
          <option value="daily">日报</option>
          <option value="instant">即时</option>
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">全部状态</option>
          <option value="success">成功</option>
          <option value="failed">失败</option>
        </select>
        <button onClick={() => refetch()} disabled={isFetching}>
          查询
        </button>
      </div>
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>事件</th>
              <th>批次</th>
              <th>文章</th>
              <th>状态</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.event}</td>
                <td>{row.batch_key}</td>
                <td>{row.article_id ?? "-"}</td>
                <td>{row.status}</td>
                <td>{new Date(row.pushed_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!data.length ? <p className="muted">暂无推送记录</p> : null}
      </div>
    </div>
  );
}
