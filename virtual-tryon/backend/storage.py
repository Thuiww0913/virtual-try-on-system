"""
storage.py — 极简 JSON 数据层
=========================================
- 数据写入做了文件锁 + 原子替换，避免并发损坏
- 所有写入操作均在 with _lock: 内执行
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "db.json"

_lock = threading.RLock()

CATEGORIES = {"upperbody", "lowerbody", "dress"}
DEFAULT_CATEGORY = "upperbody"

CATEGORY_TO_INT = {"upperbody": 0, "lowerbody": 1, "dress": 2}

DEFAULT_DB: Dict[str, Any] = {
    "version": 2,
    "clothes": [],   # [{ id, name, category, filename, url, order, created_at }]
    "models":  [],   # [{ id, name, filename, url, order, created_at }]
}


# ── 内部读写 ────────────────────────────────────────────────────────────
def _read() -> dict:
    if not DB_PATH.exists():
        _write(DEFAULT_DB)
        return json.loads(json.dumps(DEFAULT_DB))
    with DB_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # 老版本 db.json 没有 models 字段,自动补齐(保持兼容)
    if "models" not in data:
        data["models"] = []
    if "clothes" not in data:
        data["clothes"] = []
    return data


def _write(data: dict) -> None:
    """原子写入：先写临时文件再 os.replace。"""
    tmp = DB_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_PATH)


# ── 公共 API ─────────────────────────────────────────────────────────────
def list_clothes(category: Optional[str] = None) -> List[dict]:
    with _lock:
        items = list(_read()["clothes"])
    if category and category != "all":
        items = [x for x in items if x.get("category") == category]
    items.sort(key=lambda x: (x.get("order", 0), x.get("created_at", "")))
    return items


def get_cloth(cloth_id: str) -> Optional[dict]:
    with _lock:
        for x in _read()["clothes"]:
            if x["id"] == cloth_id:
                return x
    return None


def gen_id() -> str:
    return f"c_{uuid.uuid4().hex[:10]}"


def add_cloth(*, id: str, name: str, category: str, filename: str, url: str) -> dict:
    if category not in CATEGORIES:
        category = DEFAULT_CATEGORY
    item = {
        "id":         id,
        "name":       name,
        "category":   category,
        "filename":   filename,
        "url":        url,
        "order":      0,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with _lock:
        data = _read()
        if data["clothes"]:
            min_order = min((x.get("order", 0) for x in data["clothes"]), default=0)
            item["order"] = min_order - 1
        data["clothes"].append(item)
        _write(data)
    return item


def update_cloth(cloth_id: str, **fields) -> Optional[dict]:
    allowed = {"name", "category", "order"}
    with _lock:
        data = _read()
        target = None
        for x in data["clothes"]:
            if x["id"] == cloth_id:
                for k, v in fields.items():
                    if k in allowed and v is not None:
                        if k == "category" and v not in CATEGORIES:
                            v = DEFAULT_CATEGORY
                        x[k] = v
                target = x
                break
        if target:
            _write(data)
        return target


def reorder_clothes(ordered_ids: List[str]) -> int:
    """根据传入 id 列表重写 order 字段。返回更新数量。"""
    with _lock:
        data = _read()
        index = {x["id"]: x for x in data["clothes"]}
        updated = 0
        for i, cid in enumerate(ordered_ids):
            if cid in index:
                index[cid]["order"] = i
                updated += 1
        _write(data)
    return updated


def delete_cloth(cloth_id: str) -> Optional[dict]:
    with _lock:
        data = _read()
        target = None
        keep = []
        for x in data["clothes"]:
            if x["id"] == cloth_id:
                target = x
            else:
                keep.append(x)
        if target:
            data["clothes"] = keep
            _write(data)
    return target


# ── 模特(model)管理:与 clothes 完全对称,仅去掉 category ────────────────────
def list_models() -> List[dict]:
    with _lock:
        items = list(_read()["models"])
    items.sort(key=lambda x: (x.get("order", 0), x.get("created_at", "")))
    return items


def get_model(model_id: str) -> Optional[dict]:
    with _lock:
        for x in _read()["models"]:
            if x["id"] == model_id:
                return x
    return None


def gen_model_id() -> str:
    return f"m_{uuid.uuid4().hex[:10]}"


def add_model(*, id: str, name: str, filename: str, url: str) -> dict:
    item = {
        "id":         id,
        "name":       name,
        "filename":   filename,
        "url":        url,
        "order":      0,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with _lock:
        data = _read()
        if data["models"]:
            min_order = min((x.get("order", 0) for x in data["models"]), default=0)
            item["order"] = min_order - 1
        data["models"].append(item)
        _write(data)
    return item


def update_model(model_id: str, **fields) -> Optional[dict]:
    allowed = {"name", "order"}
    with _lock:
        data = _read()
        target = None
        for x in data["models"]:
            if x["id"] == model_id:
                for k, v in fields.items():
                    if k in allowed and v is not None:
                        x[k] = v
                target = x
                break
        if target:
            _write(data)
        return target


def reorder_models(ordered_ids: List[str]) -> int:
    """根据传入 id 列表重写 order 字段。返回更新数量。"""
    with _lock:
        data = _read()
        index = {x["id"]: x for x in data["models"]}
        updated = 0
        for i, mid in enumerate(ordered_ids):
            if mid in index:
                index[mid]["order"] = i
                updated += 1
        _write(data)
    return updated


def delete_model(model_id: str) -> Optional[dict]:
    with _lock:
        data = _read()
        target = None
        keep = []
        for x in data["models"]:
            if x["id"] == model_id:
                target = x
            else:
                keep.append(x)
        if target:
            data["models"] = keep
            _write(data)
    return target
