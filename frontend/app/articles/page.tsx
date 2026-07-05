"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  ACTION_LABELS,
  Article,
  fetchArticles,
  fetchUserActions,
  postUserAction,
} from "../../lib/api";

const PAGE_SIZES = [10, 20, 50] as const;

function buildActionMap(actions: { article_id: number; action: string }[]) {
  const map = new Map<number, Set<string>>();
  for (const record of actions) {
    const set = map.get(record.article_id) ?? new Set<string>();
    set.add(record.action);
    map.set(record.article_id, set);
  }
  return map;
}

function scoreClass(score: number | undefined) {
  if (score == null) return "score-badge score-none";
  if (score >= 8) return "score-badge score-high";
  if (score >= 5) return "score-badge score-mid";
  return "score-badge score-low";
}

function formatDate(value: string | null | undefined) {
  if (!value) return null;
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Pagination({
  total,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: {
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  const pages: (number | "...")[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i += 1) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i += 1) {
      pages.push(i);
    }
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
  }

  return (
    <div className="pagination">
      <div className="pagination-info">
        显示 {start}–{end} / 共 {total} 篇
      </div>
      <div className="pagination-controls">
        <label className="page-size-label">
          每页
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
          >
            {PAGE_SIZES.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="btn-secondary"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          上一页
        </button>
        <div className="page-numbers">
          {pages.map((p, idx) =>
            p === "..." ? (
              <span key={`ellipsis-${idx}`} className="page-ellipsis">
                …
              </span>
            ) : (
              <button
                key={p}
                type="button"
                className={`page-btn ${p === page ? "active" : ""}`}
                onClick={() => onPageChange(p)}
              >
                {p}
              </button>
            )
          )}
        </div>
        <button
          type="button"
          className="btn-secondary"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          下一页
        </button>
      </div>
    </div>
  );
}

function ActionToast({ message, type }: { message: string; type: "success" | "error" }) {
  return (
    <div className={`action-toast ${type === "error" ? "action-toast-error" : ""}`} role="status">
      {message}
    </div>
  );
}

function ArticleCard({
  article,
  activeActions,
  pendingKey,
  onAction,
}: {
  article: Article;
  activeActions: Set<string>;
  pendingKey: string | null;
  onAction: (id: number, action: string) => void;
}) {
  const analysis = article.analysis;
  const summary = analysis?.summary || article.summary;
  const collected = formatDate(article.collected_at);
  const published = formatDate(article.published_at);

  const actions = [
    { key: "bookmark", label: "收藏" },
    { key: "later", label: "稍后读" },
    { key: "dismiss", label: "不感兴趣", muted: true },
  ] as const;

  return (
    <article className="article-card">
      <div className="article-card-header">
        <div className="article-card-title-row">
          <span className={scoreClass(analysis?.score)}>
            {analysis?.score != null ? analysis.score.toFixed(1) : "—"}
          </span>
          <h3 className="article-title">
            <a href={article.url} target="_blank" rel="noreferrer">
              {article.title}
            </a>
          </h3>
        </div>
        <div className="article-meta">
          <span>#{article.id}</span>
          <span>源 {article.source_id}</span>
          {article.author ? <span>{article.author}</span> : null}
          {analysis?.category ? (
            <span className="category-chip">{analysis.category}</span>
          ) : null}
          {activeActions.has("bookmark") ? <span className="action-chip">已收藏</span> : null}
          {activeActions.has("later") ? <span className="action-chip action-chip-later">稍后读</span> : null}
        </div>
      </div>

      {summary ? <p className="article-summary">{summary}</p> : null}

      {Array.isArray(analysis?.tags) && analysis.tags.length > 0 ? (
        <div className="tag-list">
          {analysis.tags.map((tag) => (
            <span key={tag} className="tag">
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {analysis?.score_reason ? (
        <p className="score-reason">评分理由：{analysis.score_reason}</p>
      ) : null}

      <div className="article-card-footer">
        <div className="article-dates">
          {published ? <span>发布 {published}</span> : null}
          {collected ? <span>采集 {collected}</span> : null}
        </div>
        <div className="article-actions">
          {actions.map((item) => {
            const { key, label } = item;
            const muted = "muted" in item && item.muted;
            const isActive = activeActions.has(key);
            const isPending = pendingKey === `${article.id}:${key}`;
            return (
              <button
                key={key}
                type="button"
                className={`btn-ghost ${muted ? "btn-muted" : ""} ${isActive ? "btn-active" : ""}`}
                disabled={isPending || isActive}
                onClick={() => onAction(article.id, key)}
              >
                {isPending ? "处理中…" : isActive ? `✓ ${label}` : label}
              </button>
            );
          })}
        </div>
      </div>
    </article>
  );
}

export default function ArticlesPage() {
  const queryClient = useQueryClient();
  const [minScore, setMinScore] = useState("");
  const [appliedMinScore, setAppliedMinScore] = useState<number | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<number>(20);
  const [actionMsg, setActionMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [hiddenIds, setHiddenIds] = useState<Set<number>>(new Set());

  const offset = (page - 1) * pageSize;

  const { data: actionsData = [] } = useQuery({
    queryKey: ["user-actions"],
    queryFn: () => fetchUserActions({ limit: 2000 }),
  });

  const actionMap = useMemo(() => buildActionMap(actionsData), [actionsData]);

  const { data, refetch, isFetching, isLoading, error } = useQuery({
    queryKey: ["articles", appliedMinScore, page, pageSize],
    queryFn: () =>
      fetchArticles({
        min_score: appliedMinScore,
        limit: pageSize,
        offset,
      }),
  });

  const items = (data?.items ?? []).filter((row) => !hiddenIds.has(row.id));
  const total = data?.total ?? 0;

  useEffect(() => {
    if (!actionMsg) return;
    const timer = window.setTimeout(() => setActionMsg(null), 3000);
    return () => window.clearTimeout(timer);
  }, [actionMsg]);

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    setAppliedMinScore(minScore ? Number(minScore) : undefined);
    setPage(1);
    setHiddenIds(new Set());
  }

  function handlePageSizeChange(size: number) {
    setPageSize(size);
    setPage(1);
    setHiddenIds(new Set());
  }

  async function handleAction(articleId: number, action: string) {
    const key = `${articleId}:${action}`;
    setPendingKey(key);
    try {
      await postUserAction(articleId, action);
      await queryClient.invalidateQueries({ queryKey: ["user-actions"] });

      const label = ACTION_LABELS[action] ?? action;
      setActionMsg({ text: `已${label}（#${articleId}）`, type: "success" });

      if (action === "dismiss") {
        setHiddenIds((prev) => new Set(prev).add(articleId));
      }
    } catch {
      setActionMsg({ text: "操作失败，请确认已登录后重试", type: "error" });
    } finally {
      setPendingKey(null);
    }
  }

  return (
    <div className="page">
      {actionMsg ? <ActionToast message={actionMsg.text} type={actionMsg.type} /> : null}

      <div className="page-header">
        <div>
          <h2>文章列表</h2>
          <p className="page-desc">浏览已采集资讯，按评分筛选并分页查看</p>
        </div>
      </div>

      <form className="toolbar card toolbar-card" onSubmit={handleSearch}>
        <label className="filter-field">
          <span>最低评分</span>
          <input
            type="number"
            min={0}
            max={10}
            step={0.5}
            placeholder="不限"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value)}
          />
        </label>
        <button type="submit" disabled={isFetching}>
          {isFetching ? "查询中…" : "筛选"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => {
            setMinScore("");
            setAppliedMinScore(undefined);
            setPage(1);
            setHiddenIds(new Set());
            refetch();
          }}
        >
          重置
        </button>
      </form>

      {error ? <p className="error">加载文章失败，请稍后重试</p> : null}

      {isLoading ? (
        <div className="empty-state card">加载中…</div>
      ) : items.length === 0 ? (
        <div className="empty-state card">
          <p>暂无文章</p>
          <p className="muted">等待采集任务运行，或调低筛选条件后再试</p>
        </div>
      ) : (
        <div className="article-list">
          {items.map((row) => (
            <ArticleCard
              key={row.id}
              article={row}
              activeActions={actionMap.get(row.id) ?? new Set()}
              pendingKey={pendingKey}
              onAction={handleAction}
            />
          ))}
        </div>
      )}

      {total > 0 ? (
        <Pagination
          total={total}
          page={page}
          pageSize={pageSize}
          onPageChange={(p) => {
            setPage(p);
            setHiddenIds(new Set());
          }}
          onPageSizeChange={handlePageSizeChange}
        />
      ) : null}
    </div>
  );
}
