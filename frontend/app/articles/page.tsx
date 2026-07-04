"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchArticles, postUserAction } from "../../lib/api";

export default function ArticlesPage() {
  const [minScore, setMinScore] = useState("");
  const [actionMsg, setActionMsg] = useState("");
  const { data = [], refetch, isFetching } = useQuery({
    queryKey: ["articles", minScore],
    queryFn: () =>
      fetchArticles({
        min_score: minScore ? Number(minScore) : undefined,
        limit: 50,
      }),
  });

  async function handleAction(articleId: number, action: string) {
    try {
      await postUserAction(articleId, action);
      setActionMsg(`已记录：${action} (#${articleId})`);
    } catch {
      setActionMsg("操作失败，请重试");
    }
  }

  return (
    <div>
      <h2>文章列表</h2>
      <div className="toolbar">
        <input
          type="number"
          min={0}
          max={10}
          step={0.5}
          placeholder="最低评分"
          value={minScore}
          onChange={(e) => setMinScore(e.target.value)}
        />
        <button onClick={() => refetch()} disabled={isFetching}>
          查询
        </button>
      </div>
      {actionMsg ? <p className="muted">{actionMsg}</p> : null}
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>评分</th>
              <th>分类</th>
              <th>采集时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row: any) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>
                  <a href={row.url} target="_blank" rel="noreferrer">
                    {row.title}
                  </a>
                  {row.analysis?.summary ? (
                    <p className="muted">{row.analysis.summary.slice(0, 120)}...</p>
                  ) : null}
                </td>
                <td>{row.analysis?.score ?? "-"}</td>
                <td>{row.analysis?.category ?? "-"}</td>
                <td>{new Date(row.collected_at).toLocaleString()}</td>
                <td>
                  <div className="toolbar">
                    <button type="button" onClick={() => handleAction(row.id, "bookmark")}>
                      收藏
                    </button>
                    <button type="button" onClick={() => handleAction(row.id, "later")}>
                      稍后读
                    </button>
                    <button type="button" onClick={() => handleAction(row.id, "dismiss")}>
                      不感兴趣
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!data.length ? <p className="muted">暂无文章</p> : null}
      </div>
    </div>
  );
}
