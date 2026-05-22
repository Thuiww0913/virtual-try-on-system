"""
OOTDiffusion 远程推理 API 服务
===============================

【部署位置】
    放在远程服务器的 /root/autodl-tmp/OOTDiffusion/run/ 目录下
    即与 run_ootd.py 同级

【启动方式】
    cd /root/autodl-tmp/OOTDiffusion/run
    python api_server.py --gpu_id 0 --port 9000

【本地 SSH 端口映射】
    ssh -L 9000:127.0.0.1:9000 root@<服务器IP> -p <SSH端口>
    之后本地访问 http://127.0.0.1:9000 即可

【接口】
    POST /tryon
        form-data: person=<人像图>, cloth=<衣服图>
        返回: { "code": 0, "data": { "image_base64": "..." } }

    GET  /health   -- 检查服务及模型加载状态
"""

import io
import sys
import base64
import logging
import argparse
import traceback
import uuid
from pathlib import Path

# ── sys.path 设置（与 run_ootd.py 完全一致）────────────────────────────────
# 本文件位于 OOTDiffusion/run/api_server.py
# PROJECT_ROOT = OOTDiffusion/
RUN_DIR      = Path(__file__).absolute().parent          # OOTDiffusion/run/
PROJECT_ROOT = RUN_DIR.parent                            # OOTDiffusion/

sys.path.insert(0, str(PROJECT_ROOT))   # 使 preprocess/, ootd/ 可导入
sys.path.insert(0, str(RUN_DIR))        # 使 utils_ootd 可导入

from pathlib import Path
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import uvicorn

# ── 日志 ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ootd-api")

# ── 命令行参数 ─────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="OOTDiffusion API Server")
parser.add_argument("--gpu_id",     type=int,   default=0,           help="GPU device id")
parser.add_argument("--port",       type=int,   default=9000,        help="监听端口")
parser.add_argument("--host",       type=str,   default="127.0.0.1", help="监听地址")
parser.add_argument("--model_type", type=str,   default="hd",        help="hd 或 dc")
parser.add_argument("--n_steps",    type=int,   default=20,          help="扩散步数")
parser.add_argument("--n_samples",  type=int,   default=1,           help="每次生成张数")
parser.add_argument("--scale",      type=float, default=2.0,         help="引导强度")
args = parser.parse_args()

# ── 输出目录（与 run_ootd.py 一致）─────────────────────────────────────────
OUTPUT_DIR = RUN_DIR / "images_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 类别映射（与 run_ootd.py 一致）─────────────────────────────────────────
CATEGORY_DICT       = ["upperbody", "lowerbody", "dress"]
CATEGORY_DICT_UTILS = ["upper_body", "lower_body", "dresses"]

# ── 懒加载模型 ──────────────────────────────────────────────────────────────
_model    = None
_openpose = None
_parsing  = None


def _load_models():
    """
    首次请求时加载所有模型，之后复用。
    导入路径与 run_ootd.py 完全相同。
    """
    global _model, _openpose, _parsing
    if _model is not None:
        return

    logger.info("[init] Loading OpenPose ...")
    from preprocess.openpose.run_openpose import OpenPose
    _openpose = OpenPose(args.gpu_id)
    logger.info("[init] OpenPose loaded.")

    logger.info("[init] Loading HumanParsing ...")
    from preprocess.humanparsing.run_parsing import Parsing
    _parsing = Parsing(args.gpu_id)
    logger.info("[init] HumanParsing loaded.")

    logger.info(f"[init] Loading OOTDiffusion (model_type={args.model_type}) ...")
    if args.model_type == "hd":
        from ootd.inference_ootd_hd import OOTDiffusionHD
        _model = OOTDiffusionHD(args.gpu_id)
    elif args.model_type == "dc":
        from ootd.inference_ootd_dc import OOTDiffusionDC
        _model = OOTDiffusionDC(args.gpu_id)
    else:
        raise ValueError(f"model_type 必须是 'hd' 或 'dc'，当前值: {args.model_type}")
    logger.info("[init] All models loaded successfully.")


# ── FastAPI 应用 ────────────────────────────────────────────────────────────
app = FastAPI(title="OOTDiffusion Inference API", version="2.0.0")


@app.get("/")
def root():
    return {
        "message": "OOTDiffusion API is running",
        "model_type": args.model_type,
        "output_dir": str(OUTPUT_DIR),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": _model is not None,
        "model_type": args.model_type,
        "project_root": str(PROJECT_ROOT),
        "run_dir": str(RUN_DIR),
    }


@app.post("/tryon")
async def tryon(
    person:    UploadFile = File(...,  description="人像图片 (jpg/png)"),
    cloth:     UploadFile = File(...,  description="衣服图片 (jpg/png)"),
    category:  int        = Form(0,    description="0=upperbody, 1=lowerbody, 2=dress"),
    n_steps:   int        = Form(None, description="扩散步数，不填则用启动参数"),
    n_samples: int        = Form(None, description="生成张数，不填则用启动参数"),
    scale:     float      = Form(None, description="引导强度，不填则用启动参数"),
    seed:      int        = Form(-1,   description="随机种子，-1 表示随机"),
):
    """
    虚拟试衣推理。

    等价于命令行：
        python run_ootd.py \\
            --model_path <person_img> \\
            --cloth_path <cloth_img> \\
            --scale 2.0 --sample 1

    返回 JSON：
    {
        "code": 0,
        "msg": "success",
        "data": {
            "image_base64": "<第一张结果图的 base64 PNG>"
        }
    }
    """
    # ── 参数：Form 优先，否则用启动参数默认值 ─────────────────────────────
    _n_steps   = n_steps   if n_steps   is not None else args.n_steps
    _n_samples = n_samples if n_samples is not None else args.n_samples
    _scale     = scale     if scale     is not None else args.scale

    # ── 校验文件类型 ───────────────────────────────────────────────────────
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    for f in (person, cloth):
        if f.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型 {f.content_type}，请上传 jpg/png/webp",
            )

    # ── 校验 category ──────────────────────────────────────────────────────
    if args.model_type == "hd" and category != 0:
        raise HTTPException(
            status_code=400,
            detail="model_type='hd' 只支持 category=0 (upperbody)",
        )
    if category not in (0, 1, 2):
        raise HTTPException(status_code=400, detail="category 必须是 0/1/2")

    # ── 读取并预处理图片（与 run_ootd.py 一致：resize 到 768x1024）─────────
    try:
        person_bytes = await person.read()
        cloth_bytes  = await cloth.read()
        model_img = Image.open(io.BytesIO(person_bytes)).convert("RGB").resize((768, 1024))
        cloth_img = Image.open(io.BytesIO(cloth_bytes)).convert("RGB").resize((768, 1024))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片读取失败: {e}")

    logger.info(
        f"Received person={person.filename}({len(person_bytes)//1024}KB), "
        f"cloth={cloth.filename}({len(cloth_bytes)//1024}KB), "
        f"category={CATEGORY_DICT[category]}, steps={_n_steps}, "
        f"samples={_n_samples}, scale={_scale}, seed={seed}"
    )

    # ── 懒加载模型 ────────────────────────────────────────────────────────
    try:
        _load_models()
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"模型加载失败: {e}")

    # ── OpenPose + HumanParsing 预处理（与 run_ootd.py 完全相同逻辑）──────
    try:
        logger.info("[preprocess] Running OpenPose + HumanParsing ...")
        from utils_ootd import get_mask_location

        keypoints          = _openpose(model_img.resize((384, 512)))
        model_parse, _     = _parsing(model_img.resize((384, 512)))

        mask, mask_gray = get_mask_location(
            args.model_type,
            CATEGORY_DICT_UTILS[category],
            model_parse,
            keypoints,
        )
        mask      = mask.resize((768, 1024), Image.NEAREST)
        mask_gray = mask_gray.resize((768, 1024), Image.NEAREST)

        masked_vton_img = Image.composite(mask_gray, model_img, mask)

        # 保存 mask（方便调试，与 run_ootd.py 行为一致）
        masked_vton_img.save(str(OUTPUT_DIR / "mask.jpg"))
        logger.info("[preprocess] Done.")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"预处理失败: {e}")

    # ── 推理（与 run_ootd.py 完全相同的调用方式）─────────────────────────
    try:
        logger.info(f"[inference] Starting ...")
        images = _model(
            model_type=args.model_type,
            category=CATEGORY_DICT[category],
            image_garm=cloth_img,
            image_vton=masked_vton_img,
            mask=mask,
            image_ori=model_img,
            num_samples=_n_samples,
            num_steps=_n_steps,
            image_scale=_scale,
            seed=seed,
        )
        logger.info(f"[inference] Done. Generated {len(images)} image(s).")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"推理失败: {e}")

    # ── 保存结果图片到磁盘（与 run_ootd.py 一致，方便直接查看）──────────
    for idx, img in enumerate(images):
        save_path = OUTPUT_DIR / f"out_{args.model_type}_{idx}.png"
        img.save(str(save_path))
        logger.info(f"[save] {save_path}")

    # ── 将第一张结果编码为 base64 返回给本地 backend ──────────────────────
    try:
        buf = io.BytesIO()
        images[0].save(buf, format="PNG")
        image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"结果编码失败: {e}")

    return JSONResponse(content={
        "code": 0,
        "msg": "success",
        "data": {
            "image_base64": image_b64
        }
    })


# ── 入口 ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"Project root : {PROJECT_ROOT}")
    logger.info(f"Run dir      : {RUN_DIR}")
    logger.info(f"Output dir   : {OUTPUT_DIR}")
    logger.info(f"Model type   : {args.model_type}")
    logger.info(f"Listening on : {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
