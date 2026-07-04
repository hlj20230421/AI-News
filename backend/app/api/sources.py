"""信息源 CRUD 端点。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import SourceCreate, SourceOut, SourceUpdate
from app.db import get_db
from app.db.models import Source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)) -> list[Source]:
    rows = list(db.execute(select(Source).order_by(Source.id)).scalars())
    return rows


@router.post("", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)) -> Source:
    src = Source(
        name=payload.name,
        url=payload.url,
        type=payload.type,
        description=payload.description,
        enabled=payload.enabled,
    )
    db.add(src)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="URL 已存在") from exc
    db.refresh(src)
    return src


@router.get("/{source_id}", response_model=SourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    src = db.get(Source, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Source 不存在")
    return src


@router.patch("/{source_id}", response_model=SourceOut)
def update_source(
    source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)
) -> Source:
    src = db.get(Source, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Source 不存在")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(src, k, v)
    db.commit()
    db.refresh(src)
    return src


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: int, db: Session = Depends(get_db)) -> None:
    src = db.get(Source, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Source 不存在")
    db.delete(src)
    db.commit()
