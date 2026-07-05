"""文章查询端点。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, nullslast, select
from sqlalchemy.orm import Session, joinedload

from app.api.schemas import ArticleOut
from app.db import get_db
from app.db.models import Analysis, Article

router = APIRouter(prefix="/articles", tags=["articles"])


def _articles_base_stmt(
    *,
    source_id: int | None,
    min_score: float | None,
):
    stmt = (
        select(Article)
        .outerjoin(Analysis, Analysis.article_id == Article.id)
        .order_by(nullslast(Analysis.score.desc()), Article.collected_at.desc())
    )

    if source_id is not None:
        stmt = stmt.where(Article.source_id == source_id)

    if min_score is not None:
        stmt = stmt.where(Analysis.score >= min_score)

    return stmt


@router.get("", response_model=list[ArticleOut])
def list_articles(
    response: Response,
    source_id: int | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0, le=10),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Article]:
    base = _articles_base_stmt(source_id=source_id, min_score=min_score)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    response.headers["X-Total-Count"] = str(total)

    rows = list(
        db.execute(
            base.options(joinedload(Article.analysis)).offset(offset).limit(limit)
        )
        .unique()
        .scalars()
    )
    return rows


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)) -> Article:
    article = db.execute(
        select(Article)
        .options(joinedload(Article.analysis))
        .where(Article.id == article_id)
    ).scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article 不存在")
    return article
