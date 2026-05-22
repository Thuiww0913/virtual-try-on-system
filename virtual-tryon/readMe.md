# 虚拟试衣系统 — 运行手册

> 最后更新：2026-03-28

---

## 一、项目结构

```
virtual-tryon/
├── backend/                  # 本地中转后端 (FastAPI)
│   ├── main.py               # 主程序，转发请求到远程模型
│   ├── model.py              # Mock 试衣（调试用，不调用真实模型）
│   ├── requirements.txt
│   ├── static/               # 结果图片存放目录
│   └── .venv/                # Python 虚拟环境
├── frontend/                 # 前端 (Vue 3 + Vite + Tailwind)
│   ├── src/
│   │   ├── App.vue
│   │   └── components/UploadCard.vue
│   ├── package.json
│   └── vite.config.js
└── OOTDiffusion/             # 模型代码（本地仅供参考，实际跑在远程服务器）
    └── run/
        ├── run_ootd.py       # 原始命令行推理脚本
        ├── utils_ootd.py     # 掩码生成工具
        └── api_server.py     # ✅ 部署到远程服务器的 API 服务
```

---

## 二、远程服务器部署

### 2.1 服务器目录结构（autodl）

```
/root/autodl-tmp/OOTDiffusion/
├── checkpoints/
│   ├── clip-vit-large-patch14/
│   ├── ootd/
│   │   ├── vae/
│   │   ├── tokenizer/
│   │   ├── text_encoder/
│   │   ├── scheduler/
│   │   ├── model_index.json
│   │   ├── ootd_hd/checkpoint-36000/
│   │   │   ├── unet_garm/
│   │   │   └── unet_vton/
│   │   └── ootd_dc/checkpoint-36000/
│   │       ├── unet_garm/
│   │       └── unet_vton/
│   ├── humanparsing/
│   │   ├── parsing_atr.onnx
│   │   └── parsing_lip.onnx
│   └── openpose/
│       └── ckpts/
│           └── body_pose_model.pth
├── ootd/
├── preprocess/
└── run/
    ├── run_ootd.py
    ├── utils_ootd.py
    └── api_server.py         ← 上传到这里
```

### 2.2 上传 api_server.py 到服务器

```bash
# 在本地执行（替换 <端口> 和 <IP>）
scp -P <SSH端口> \
  virtual-tryon/OOTDiffusion/run/api_server.py \
  root@<服务器IP>:/root/autodl-tmp/OOTDiffusion/run/api_server.py
```

### 2.3 安装 API 服务依赖（仅首次）

```bash
# 在远程服务器执行
pip install fastapi uvicorn python-multipart
```

### 2.4 启动远程 API 服务 

```bash
# 在远程服务器执行
cd /root/autodl-tmp/OOTDiffusion/run

# 推荐：用 nohup 后台运行，关闭 SSH 也不停
nohup python api_server.py \
  --gpu_id 0 \
  --port 9000 \
  --model_type hd \
  --n_samples 1 \
  --scale 2.0 \
  > api_server.log 2>&1 &

echo "API server PID: $!"
```

> 如需前台运行方便看日志：
> ```bash
> python api_server.py --gpu_id 0 --port 9000
> ```

### 2.5 验证远程服务正常

```bash
# 在远程服务器本机测试
curl http://127.0.0.1:9000/health
# 预期返回：{"status": "ok", "model_loaded": false}

# 发一张测试请求（首次会加载模型，等待约 1-2 分钟）
curl -X POST http://127.0.0.1:9000/tryon \
  -F "person=@./examples/model/01008_00.jpg" \
  -F "cloth=@./examples/garment/00055_00.jpg"
```

---

## 三、本地启动步骤

### 3.1 建立 SSH 端口映射（必须保持运行）

```bash
# 新开一个终端，保持不关闭
ssh -L 9000:127.0.0.1:9000 root@<服务器IP> -p <SSH端口>
```

autodl 平台的 SSH 命令在控制台「SSH 连接」里可以直接复制，格式类似：
```bash
ssh -L 9000:127.0.0.1:9000 root@region-xx.autodl.com -p 3xxxx
```

### 3.2 启动本地后端

```bash
cd virtual-tryon/backend

# 激活虚拟环境
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate          # Windows

# 启动后端（支持热更新）
uvicorn main:app --reload --port 8000
```

> ⚠️ 如果提示权限问题（macOS Cursor 沙箱），改用：
> ```bash
> /tmp/vtryon-venv/bin/uvicorn main:app --reload --port 8000
> ```

验证后端正常：
```bash
curl http://localhost:8000/health
# 期望：{"backend": "ok", "remote_service": "ok", ...}
```

### 3.3 启动前端

```bash
# 前端代码在 /tmp/vtryon-frontend（因 macOS 沙箱限制）
cd /tmp/vtryon-frontend
npm run dev
```

> 如果 /tmp/vtryon-frontend 被清空（重启后），重新执行：
> ```bash
> cp -r virtual-tryon/frontend /tmp/vtryon-frontend
> cd /tmp/vtryon-frontend
> npm install --cache /tmp/npm-cache
> npm run dev
> ```

### 3.4 打开浏览器

```
http://localhost:5173
```

---

## 四、完整数据流

```
浏览器 (localhost:5173)
  │  FormData { person: File, cloth: File }
  │  POST /api/tryon
  ▼
本地 backend (localhost:8000)  [backend/main.py]
  │  multipart/form-data 原样转发
  │  POST http://127.0.0.1:9000/tryon
  ▼
SSH 隧道 (localhost:9000 → 远程:9000)
  ▼
远程 GPU 服务器 (AutoDL)
  │  OOTDiffusion 推理（OpenPose → HumanParsing → Diffusion）
  │  JSON { code:0, data: { image_base64: "..." } }
  ▼
本地 backend
  │  base64 解码 → 保存为 backend/static/result_xxxx.jpg
  │  JSON { code:0, data: { image_url: "/static/result_xxxx.jpg" } }
  ▼
浏览器展示结果图片
```

---

## 五、环境变量（可选）

在启动后端前设置，用于覆盖默认值：

```bash
# 远程推理服务地址（默认已是 SSH 映射后的地址）
export REMOTE_TRYON_URL="http://127.0.0.1:9000/tryon"

# 推理超时时间（秒），模型首次加载较慢，建议设长
export REMOTE_TIMEOUT=300
```

---

## 六、api_server.py 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--gpu_id` | `0` | 使用第几块 GPU |
| `--port` | `9000` | 监听端口 |
| `--host` | `127.0.0.1` | 监听地址，只本机访问用 127.0.0.1 |
| `--model_type` | `hd` | `hd`=半身高清 / `dc`=全身 |
| `--n_steps` | `20` | 扩散步数，越高越慢越好 |
| `--n_samples` | `1` | 每次生成几张，API 只返回第一张 |
| `--scale` | `2.0` | 引导强度，越高越贴近衣服原图 |

---

## 七、Mock 模式（无远程服务器时调试）

如果远程服务器未启动，本地后端会返回 502 错误。

如需在本地用 Pillow Mock 调试前端，临时修改 `backend/main.py`：
将 `REMOTE_TRYON_URL` 对应的请求逻辑替换为直接调用 `model.py` 中的 `mock_virtual_tryon`。
`backend/model.py` 已经写好 Mock 逻辑，可直接复用。

---

## 八、常见问题

### Q: `curl health` 返回 `remote_service: unreachable`
**A:** 检查以下三点：
1. 远程服务器上 `api_server.py` 是否在运行（`ps aux | grep api_server`）
2. SSH 端口映射终端是否还开着
3. 端口是否一致（两边都是 9000）

### Q: 首次请求很慢（1-2 分钟）
**A:** 正常现象。第一次请求会触发模型懒加载（OOTDiffusion 权重加载到 GPU 需要时间），之后的请求会快很多。

### Q: `npm install` 权限报错
**A:** macOS Cursor 沙箱限制。在系统终端（iTerm/Terminal.app）中执行 `npm install`，或用 `/tmp` 目录绕过。

### Q: 前端图片不更新（显示旧结果）
**A:** 已处理，每次结果 URL 带时间戳（`?t=xxxxxxxx`）防止浏览器缓存。

---

## 九、快速启动检查清单

每次使用前按顺序检查：

- [ ] 远程服务器 `api_server.py` 正在运行
- [ ] 本地 SSH 端口映射终端保持开启（9000→9000）
- [ ] `curl http://localhost:8000/health` 返回 `remote_service: ok`
- [ ] 本地后端 `uvicorn` 在运行（端口 8000）
- [ ] 前端 `npm run dev` 在运行（端口 5173）
- [ ] 浏览器访问 `http://localhost:5173`
