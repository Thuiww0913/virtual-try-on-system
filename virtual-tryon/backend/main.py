"""
Virtual Try-On — 本地中转后端
==============================
接收前端上传的图片，转发到远程 OOTDiffusion 推理服务，
将结果图片保存到本地 static/ 目录并返回 URL 给前端。

远程服务地址通过环境变量 REMOTE_TRYON_URL 配置，
默认为 http://127.0.0.1:9000/tryon（SSH 端口映射后访问）。

启动方式：
    uvicorn main:app --reload --port 8000
"""

import io
import uuid
import base64
import logging
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from PIL import Image

import storage
from admin import router as admin_router

# ── 日志 ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("backend")

# ── 远程 OOTDiffusion 推理服务配置 ─────────────────────────────────────────
#
# OOTDiffusion 有两个权重：
#   - hd 模型：仅支持 upperbody，但效果最佳（VITON-HD 训练）
#   - dc 模型：支持 upperbody/lowerbody/dress 三类，但上半身效果略差
#
# 推荐做法：在远程同时跑两个 api_server.py，分别监听不同端口：
#
#   # 终端 1：HD 服务（专攻上半身）
#   python api_server.py --gpu_id 0 --port 9000 --model_type hd --n_samples 4 --scale 2.0
#
#   # 终端 2：DC 服务（处理下半身 / 连衣裙）
#   python api_server.py --gpu_id 0 --port 9001 --model_type dc --n_samples 4 --scale 2.0
#
# 本地通过 SSH 映射两个端口：
#   ssh -L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001 user@server
#
# 然后本地按 category 自动路由到对应实例。
#
# 如果你某段时间只跑了一个服务，把对应的 URL 改成另一个即可（两个填一样的也行）。
REMOTE_TRYON_URL_HD = "http://127.0.0.1:9000/tryon"   # upperbody → HD
REMOTE_TRYON_URL_DC = "http://127.0.0.1:9001/tryon"   # lowerbody / dress → DC

# 转发请求超时（秒）：OOTDiffusion 推理较慢，默认给 5 分钟
REMOTE_TIMEOUT = 300

logger.info(f"Remote tryon URL (HD, upperbody)        : {REMOTE_TRYON_URL_HD}")
logger.info(f"Remote tryon URL (DC, lowerbody/dress)  : {REMOTE_TRYON_URL_DC}")
logger.info(f"Remote timeout                          : {REMOTE_TIMEOUT}s")


def pick_remote_url(category: str) -> str:
    """
    根据服装类别选择远程推理服务地址：
      - upperbody          → HD 模型（质量更好）
      - lowerbody / dress  → DC 模型（HD 模型不支持这两类）
    """
    if category == "upperbody":
        return REMOTE_TRYON_URL_HD
    return REMOTE_TRYON_URL_DC

# ── 目录初始化 ──────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
STATIC_DIR  = BASE_DIR / "static"
CLOTHES_DIR = STATIC_DIR / "clothes"
STATIC_DIR.mkdir(exist_ok=True)
CLOTHES_DIR.mkdir(exist_ok=True)

# ── FastAPI 应用 ────────────────────────────────────────────────────────────
app = FastAPI(title="Virtual Try-On Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 注册管理后台路由
app.include_router(admin_router)


@app.get("/api/clothes")
def public_list_clothes(category: Optional[str] = Query(None, description="可选分类过滤")):
    """对外公开的衣服列表（前台 Dock 调用）。"""
    return {"code": 0, "data": storage.list_clothes(category=category)}


# ── 工具函数 ───────────────────────────────────────────────────────────────
def _save_base64_image(b64_str: str, filename: str) -> Path:
    """
    将 base64 编码的 PNG 图片字符串解码并保存为 JPEG 文件。
    返回保存路径。
    """
    img_bytes = base64.b64decode(b64_str)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    out_path = STATIC_DIR / filename
    img.save(str(out_path), format="JPEG", quality=95)
    logger.info(f"Result image saved -> {out_path}")
    return out_path


# ── 路由 ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Virtual Try-On backend is running", "version": "2.0.0"}


@app.get("/health")
def health():
    """检查本地后端及两个远程推理服务（HD / DC）是否可达。"""
    def _check(url: str) -> dict:
        try:
            health_url = url.replace("/tryon", "/health")
            resp = requests.get(health_url, timeout=5)
            return {
                "url": url,
                "status": "ok" if resp.status_code == 200 else "unreachable",
                "detail": resp.json().get("status", "unknown") if resp.status_code == 200 else resp.text[:120],
            }
        except Exception as e:
            return {"url": url, "status": "unreachable", "detail": str(e)}

    hd = _check(REMOTE_TRYON_URL_HD)
    dc = _check(REMOTE_TRYON_URL_DC)
    return {
        "backend": "ok",
        "remote_hd": hd,
        "remote_dc": dc,
    }


@app.post("/api/tryon")
async def tryon(
    person:   UploadFile    = File(..., description="人像图片"),
    cloth:    UploadFile    = File(..., description="衣服图片"),
    category: Optional[str] = Form(
        "upperbody",
        description="服装类别：upperbody / lowerbody / dress",
    ),
):
    """
    数据流：
      前端  --multipart/form-data + category-->  本地 backend
      本地 backend  --multipart/form-data + category(int)-->  远程 OOTDiffusion API
      远程 OOTDiffusion API  --JSON{image_base64}-->  本地 backend
      本地 backend  --JSON{image_url}-->  前端

    远程 OOTDiffusion 接受的 category 是整数 0/1/2，分别对应：
      0 = upperbody (上半身)
      1 = lowerbody (下半身)
      2 = dress     (连衣裙)
    要使用 1 / 2，远程 api_server.py 必须以 --model_type dc 启动。
    """
    # ── 1. 校验文件类型 ────────────────────────────────────────────────────
    allowed = {"image/jpeg", "image/png", "image/webp"}
    for f in (person, cloth):
        if f.content_type not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型 {f.content_type}，请上传 jpg/png/webp 图片",
            )

    # ── 2. 校验并转换 category ────────────────────────────────────────────
    cat_str = (category or "upperbody").lower()
    if cat_str not in storage.CATEGORY_TO_INT:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的 category={category}，必须是 upperbody / lowerbody / dress",
        )
    cat_int = storage.CATEGORY_TO_INT[cat_str]

    # ── 3. 读取图片字节流 ──────────────────────────────────────────────────
    person_bytes = await person.read()
    cloth_bytes  = await cloth.read()
    logger.info(
        f"Received person={person.filename} ({len(person_bytes)//1024}KB), "
        f"cloth={cloth.filename} ({len(cloth_bytes)//1024}KB), "
        f"category={cat_str}({cat_int})"
    )

    # ── 4. 转发到远程推理服务（按类别选择 hd / dc） ───────────────────────
    remote_url = pick_remote_url(cat_str)
    logger.info(f"Forwarding to remote ({cat_str}): {remote_url}")
    try:
        remote_resp = requests.post(
            remote_url,
            files={
                "person": (person.filename, person_bytes, person.content_type),
                "cloth":  (cloth.filename,  cloth_bytes,  cloth.content_type),
            },
            data={
                "category": str(cat_int),
            },
            timeout=REMOTE_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to remote service")
        raise HTTPException(
            status_code=502,
            detail=(
                f"无法连接远程推理服务 {remote_url}。\n"
                "请确认：\n"
                "1. 远程服务器已运行 api_server.py\n"
                "2. SSH 端口映射已建立：ssh -L 9000:127.0.0.1:9000 user@server"
            ),
        )
    except requests.exceptions.Timeout:
        logger.error("Remote service timed out")
        raise HTTPException(
            status_code=504,
            detail=f"远程推理服务超时（>{REMOTE_TIMEOUT}s），请增大 REMOTE_TIMEOUT 环境变量",
        )
    except Exception as e:
        logger.error(f"Remote request failed: {e}")
        raise HTTPException(status_code=502, detail=f"转发请求失败: {e}")

    # ── 4. 解析远程返回结果 ────────────────────────────────────────────────
    if remote_resp.status_code != 200:
        logger.error(f"Remote returned {remote_resp.status_code}: {remote_resp.text[:300]}")
        raise HTTPException(
            status_code=502,
            detail=f"远程推理服务返回错误 {remote_resp.status_code}: {remote_resp.text[:300]}",
        )

    try:
        remote_json = remote_resp.json()
        if remote_json.get("code") != 0:
            raise ValueError(remote_json.get("msg", "unknown error"))
        image_b64 = remote_json["data"]["image_base64"]
    except Exception as e:
        logger.error(f"Failed to parse remote response: {e}")
        raise HTTPException(status_code=502, detail=f"解析远程结果失败: {e}")

    # ── 5. 解码 base64 并保存到本地 static/ ───────────────────────────────
    result_filename = f"result_{uuid.uuid4().hex[:8]}.jpg"
    try:
        _save_base64_image(image_b64, result_filename)
    except Exception as e:
        logger.error(f"Failed to save result image: {e}")
        raise HTTPException(status_code=500, detail=f"保存结果图片失败: {e}")

    # ── 6. 返回图片 URL 给前端 ─────────────────────────────────────────────
    logger.info(f"Tryon complete -> /static/{result_filename}")
    return JSONResponse(content={
        "code": 0,
        "msg": "success",
        "data": {
            "image_url": f"/static/{result_filename}"
        },
    })
