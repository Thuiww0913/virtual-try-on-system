"""
admin.py — 后台管理路由
========================
- 简单密码认证：登录后返回随机 token，存入内存集合
- token 有效期通过创建时间判断（默认 7 天）
- 所有 /api/admin/* 路由需在 Header 携带 `Authorization: Bearer <token>`

环境变量：
    ADMIN_PASSWORD     管理员密码（默认 admin123）
    ADMIN_TOKEN_TTL    Token 有效期（秒，默认 604800 = 7 天）
"""

from __future__ import annotations

import io
import os
import secrets
import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Header
from PIL import Image
from pydantic import BaseModel

import storage

logger = logging.getLogger("backend.admin")

# ── 配置 ───────────────────────────────────────────────────────────────────
ADMIN_PASSWORD  = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_TOKEN_TTL = int(os.getenv("ADMIN_TOKEN_TTL", "604800"))   # 7 days

BASE_DIR    = Path(__file__).parent
CLOTHES_DIR = BASE_DIR / "static" / "clothes"
MODELS_DIR  = BASE_DIR / "static" / "models"
CLOTHES_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# 内存 token 存储：{ token: created_ts }
# 进程重启后所有人需要重新登录，对小型管理后台够用
_TOKENS: dict[str, float] = {}

logger.info(f"Admin password set: {'<custom>' if os.getenv('ADMIN_PASSWORD') else '<default: admin123>'}")
logger.info(f"Token TTL: {ADMIN_TOKEN_TTL}s")


# ── 鉴权 ───────────────────────────────────────────────────────────────────
def _issue_token() -> str:
    token = secrets.token_urlsafe(32)
    _TOKENS[token] = time.time()
    _gc_tokens()
    return token


def _gc_tokens() -> None:
    """清理过期 token。"""
    now = time.time()
    expired = [t for t, ts in _TOKENS.items() if now - ts > ADMIN_TOKEN_TTL]
    for t in expired:
        _TOKENS.pop(t, None)


def require_admin(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="缺少认证 token")
    token = authorization.split(" ", 1)[1].strip()
    ts = _TOKENS.get(token)
    if ts is None:
        raise HTTPException(status_code=401, detail="token 无效，请重新登录")
    if time.time() - ts > ADMIN_TOKEN_TTL:
        _TOKENS.pop(token, None)
        raise HTTPException(status_code=401, detail="token 已过期，请重新登录")
    return token


# ── 路由 ───────────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginPayload(BaseModel):
    password: str


@router.post("/login")
def login(payload: LoginPayload):
    """管理员登录，返回 token。"""
    if not secrets.compare_digest(payload.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="密码错误")
    token = _issue_token()
    return {
        "code": 0,
        "msg":  "login success",
        "data": { "token": token, "ttl": ADMIN_TOKEN_TTL },
    }


@router.post("/logout")
def logout(token: str = Depends(require_admin)):
    _TOKENS.pop(token, None)
    return {"code": 0, "msg": "logout success"}


@router.get("/check")
def check(_: str = Depends(require_admin)):
    """检查 token 是否仍然有效。"""
    return {"code": 0, "msg": "ok"}


@router.get("/clothes")
def list_clothes(_: str = Depends(require_admin)):
    return {"code": 0, "data": storage.list_clothes()}


@router.post("/clothes")
async def upload_clothes(
    files:    list[UploadFile] = File(..., description="衣服图片，支持多文件"),
    category: str              = Form("other"),
    name:     Optional[str]    = Form(None),
    _:        str              = Depends(require_admin),
):
    """
    批量上传衣服。每张图片：
    - 转码为 JPEG（最长边 800px）
    - 写入 static/clothes/
    - 写入 db.json
    返回所有新创建的衣服记录。
    """
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    allowed = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    created = []
    for f in files:
        if f.content_type not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"{f.filename} 文件类型不支持（{f.content_type}），仅支持 jpg/png/webp",
            )

        raw = await f.read()
        try:
            img = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{f.filename} 不是有效的图片：{e}")

        # 缩放到最长边 800
        img.thumbnail((800, 800), Image.LANCZOS)

        cid      = storage.gen_id()
        filename = f"{cid}.jpg"
        out_path = CLOTHES_DIR / filename
        img.save(out_path, format="JPEG", quality=88, optimize=True)

        item = storage.add_cloth(
            id       = cid,
            name     = (name or Path(f.filename).stem)[:60],
            category = category,
            filename = filename,
            url      = f"/static/clothes/{filename}",
        )
        created.append(item)

    logger.info(f"Uploaded {len(created)} clothes ({category})")
    return {"code": 0, "data": created}


class UpdatePayload(BaseModel):
    name: Optional[str]     = None
    category: Optional[str] = None
    order: Optional[int]    = None


@router.patch("/clothes/{cloth_id}")
def update_one(cloth_id: str, payload: UpdatePayload, _: str = Depends(require_admin)):
    item = storage.update_cloth(
        cloth_id,
        name     = payload.name,
        category = payload.category,
        order    = payload.order,
    )
    if not item:
        raise HTTPException(status_code=404, detail="衣服不存在")
    return {"code": 0, "data": item}


class ReorderPayload(BaseModel):
    ids: list[str]


@router.put("/clothes/order")
def reorder(payload: ReorderPayload, _: str = Depends(require_admin)):
    n = storage.reorder_clothes(payload.ids)
    return {"code": 0, "msg": f"reordered {n} items"}


@router.delete("/clothes/{cloth_id}")
def delete_one(cloth_id: str, _: str = Depends(require_admin)):
    item = storage.delete_cloth(cloth_id)
    if not item:
        raise HTTPException(status_code=404, detail="衣服不存在")
    # 同步删除文件
    try:
        (CLOTHES_DIR / item["filename"]).unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"Failed to remove file {item['filename']}: {e}")
    return {"code": 0, "data": item}


# ── 模特相册管理路由 ─────────────────────────────────────────────────────
@router.get("/models")
def list_models(_: str = Depends(require_admin)):
    return {"code": 0, "data": storage.list_models()}


@router.post("/models")
async def upload_models(
    files: list[UploadFile] = File(..., description="模特图片,支持多文件"),
    name:  Optional[str]    = Form(None),
    _:     str              = Depends(require_admin),
):
    """
    批量上传模特(人像)图片。每张图片：
    - 转码为 JPEG(最长边 1024px,比衣服图保留更多细节以利于试穿)
    - 写入 static/models/
    - 写入 db.json
    """
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    allowed = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    created = []
    for f in files:
        if f.content_type not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"{f.filename} 文件类型不支持({f.content_type}),仅支持 jpg/png/webp",
            )

        raw = await f.read()
        try:
            img = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{f.filename} 不是有效的图片:{e}")

        img.thumbnail((1024, 1024), Image.LANCZOS)

        mid      = storage.gen_model_id()
        filename = f"{mid}.jpg"
        out_path = MODELS_DIR / filename
        img.save(out_path, format="JPEG", quality=90, optimize=True)

        item = storage.add_model(
            id       = mid,
            name     = (name or Path(f.filename).stem)[:60],
            filename = filename,
            url      = f"/static/models/{filename}",
        )
        created.append(item)

    logger.info(f"Uploaded {len(created)} models")
    return {"code": 0, "data": created}


class UpdateModelPayload(BaseModel):
    name:  Optional[str] = None
    order: Optional[int] = None


@router.patch("/models/{model_id}")
def update_model_one(model_id: str, payload: UpdateModelPayload, _: str = Depends(require_admin)):
    item = storage.update_model(
        model_id,
        name  = payload.name,
        order = payload.order,
    )
    if not item:
        raise HTTPException(status_code=404, detail="模特不存在")
    return {"code": 0, "data": item}


@router.put("/models/order")
def reorder_models_route(payload: ReorderPayload, _: str = Depends(require_admin)):
    n = storage.reorder_models(payload.ids)
    return {"code": 0, "msg": f"reordered {n} models"}


@router.delete("/models/{model_id}")
def delete_model_one(model_id: str, _: str = Depends(require_admin)):
    item = storage.delete_model(model_id)
    if not item:
        raise HTTPException(status_code=404, detail="模特不存在")
    try:
        (MODELS_DIR / item["filename"]).unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"Failed to remove file {item['filename']}: {e}")
    return {"code": 0, "data": item}
