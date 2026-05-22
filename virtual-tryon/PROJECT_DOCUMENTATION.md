# 虚拟试衣系统项目说明文档

## 1. 项目概述

本项目是一个基于 `Vue 3 + FastAPI + OOTDiffusion` 的虚拟试衣系统，采用“前端 + 本地中转后端 + 远程 GPU 推理服务”的分层架构。

系统核心目标是：

- 用户上传人物图和衣服图。
- 系统调用远程 OOTDiffusion 模型进行试衣生成。
- 前端展示并支持下载试衣结果。

该架构把深度学习推理与本地业务解耦，便于开发调试与部署扩展。

## 2. 项目目录结构

```text
virtual-tryon/
├── frontend/                        # 前端：Vue3 + Vite + Tailwind
│   ├── src/
│   │   ├── App.vue                 # 单页主逻辑：上传、提交、结果展示
│   │   ├── main.js
│   │   ├── style.css
│   │   └── components/UploadCard.vue
│   ├── package.json
│   └── vite.config.js              # /api /static 代理到本地后端
├── backend/                         # 本地后端：FastAPI
│   ├── main.py                     # 接口入口，转发请求到远程推理
│   ├── model.py                    # 本地 mock 试衣逻辑（调试用途）
│   ├── requirements.txt
│   └── static/                     # 结果图落盘目录
├── OOTDiffusion/                    # 模型工程（主要运行在远程服务器）
│   └── run/
│       ├── api_server.py           # 远程推理 API 服务
│       ├── run_ootd.py             # 原始命令行推理脚本
│       └── utils_ootd.py
├── readMe.md                        # 运行手册
└── start.sh                         # 本地一键启动脚本
```

## 3. 技术栈

## 3.1 前端

- `Vue 3`：页面与状态管理。
- `Vite`：开发构建工具。
- `Tailwind CSS`：页面样式和原子化类。
- `Axios`：HTTP 请求。

关键版本来自 `frontend/package.json`：

- `vue ^3.4.21`
- `vite ^5.2.8`
- `tailwindcss ^3.4.3`
- `axios ^1.6.8`

## 3.2 本地后端

- `FastAPI`：Web API 框架。
- `Uvicorn`：ASGI 运行器。
- `requests`：转发远程请求。
- `Pillow`：解码远程返回的 Base64 图片并保存。
- `python-multipart`：处理表单文件上传。

关键版本来自 `backend/requirements.txt`：

- `fastapi==0.111.0`
- `uvicorn[standard]==0.29.0`
- `python-multipart==0.0.9`
- `Pillow==10.3.0`
- `requests==2.32.3`

## 3.3 远程推理服务

- `OOTDiffusion`：虚拟试衣扩散模型。
- `OpenPose`：关键点提取。
- `HumanParsing`：人体分割。
- `FastAPI + Uvicorn`：对外暴露推理接口。

## 4. 系统架构与数据流

## 4.1 架构分层

- 表现层：前端页面，负责交互与展示。
- 应用层：本地 FastAPI，负责输入校验、转发、结果管理。
- 算法层：远程 OOTDiffusion，负责真实推理。

## 4.2 端到端数据流

```text
Browser(Vue) 
  -> POST /api/tryon (person, cloth)
Local Backend(FastAPI:8000)
  -> POST REMOTE_TRYON_URL (默认 http://127.0.0.1:9000/tryon)
SSH Tunnel
Remote OOTDiffusion API(FastAPI:9000)
  -> OpenPose + Parsing + Diffusion
  -> JSON(code=0, data.image_base64)
Local Backend
  -> base64 decode + save backend/static/result_xxxx.jpg
  -> JSON(code=0, data.image_url)
Browser
  -> 展示 /static/result_xxxx.jpg
```

## 5. 核心模块实现说明

## 5.1 前端主流程（`frontend/src/App.vue`）

核心状态：

- `personFile`：人物文件。
- `clothFile`：衣服文件。
- `personPreview`、`clothPreview`：本地预览 URL。
- `loading`：请求进行中状态。
- `resultUrl`：结果图 URL。
- `error`：错误信息。

核心流程：

1. 用户上传人物图和衣服图。
2. 前端构造 `FormData`。
3. `axios.post('/api/tryon', formData)` 请求本地后端。
4. 成功后显示 `resultUrl`，失败显示错误文案。

说明：

- 前端通过 `?t=Date.now()` 防缓存，避免结果图同名时被浏览器缓存。

## 5.2 上传组件（`frontend/src/components/UploadCard.vue`）

支持两种输入方式：

- 点击上传。
- 拖拽上传。

实现要点：

- 内部隐藏 `<input type="file">`。
- 对外抛出 `change` 事件，把文件对象传给父组件。
- 可重复选择同一文件（重置 `input` 值）。

## 5.3 本地后端转发（`backend/main.py`）

职责：

- 校验文件类型（`jpeg/png/webp`）。
- 从表单读取 `person` 与 `cloth`。
- 使用 `requests.post` 转发到远程推理服务。
- 解析远程 JSON，读取 `image_base64`。
- 保存结果图到 `backend/static`。
- 返回可直接访问的图片 URL。

健康检查：

- `GET /health` 会探测远程服务可达性并返回 `remote_service` 状态。

## 5.4 远程推理 API（`OOTDiffusion/run/api_server.py`）

职责：

- 接收 `person`、`cloth`、`category` 等参数。
- 首次请求懒加载模型。
- 执行人体关键点与分割预处理。
- 调用 OOTDiffusion 推理生成结果。
- 返回第一张结果图的 Base64 编码。

实现细节：

- 入参图像统一 resize 到 `768x1024`。
- `model_type='hd'` 时只支持 `category=0`（upperbody）。
- 支持通过表单覆盖推理参数：`n_steps`、`n_samples`、`scale`、`seed`。

## 6. API 设计说明

## 6.1 本地后端接口

### 6.1.1 `GET /`

用途：后端服务存活检查。

示例响应：

```json
{
  "message": "Virtual Try-On backend is running",
  "version": "2.0.0"
}
```

### 6.1.2 `GET /health`

用途：检查本地服务与远程推理连通性。

示例响应：

```json
{
  "backend": "ok",
  "remote_service": "ok",
  "remote_detail": "ok",
  "remote_url": "http://127.0.0.1:9000/tryon"
}
```

### 6.1.3 `POST /api/tryon`

请求类型：`multipart/form-data`

请求字段：

- `person`: 人像图文件（必填）。
- `cloth`: 衣服图文件（必填）。

示例请求：

```bash
curl -X POST http://127.0.0.1:8000/api/tryon \
  -F "person=@./person.jpg" \
  -F "cloth=@./cloth.jpg"
```

成功响应：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "image_url": "/static/result_a1b2c3d4.jpg"
  }
}
```

常见错误：

- `400`：文件类型不支持。
- `502`：远程服务不可达或远程返回错误。
- `504`：远程推理超时。
- `500`：结果图保存失败。

## 6.2 远程推理接口

### 6.2.1 `GET /`

用途：查看远程服务基本信息。

### 6.2.2 `GET /health`

用途：查看模型是否已加载。

示例响应：

```json
{
  "status": "ok",
  "model_loaded": false,
  "model_type": "hd"
}
```

### 6.2.3 `POST /tryon`

请求类型：`multipart/form-data`

请求字段：

- `person`: 人像图文件（必填）。
- `cloth`: 衣服图文件（必填）。
- `category`: 0/1/2，默认 0。
- `n_steps`: 可选，扩散步数。
- `n_samples`: 可选，生成数量。
- `scale`: 可选，引导系数。
- `seed`: 可选，默认 -1（随机）。

成功响应：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "image_base64": "iVBORw0KGgoAAA..."
  }
}
```

## 7. 部署与运行说明

## 7.1 运行前提

- 本地已安装 Python 与 Node.js。
- 远程 GPU 服务可运行 OOTDiffusion。
- 本地与远程建立 SSH 端口映射。

## 7.2 本地后端启动

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

## 7.3 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 7.4 远程服务启动

```bash
cd /root/autodl-tmp/OOTDiffusion/run
python api_server.py --gpu_id 0 --port 9000 --model_type hd --n_samples 1 --scale 2.0
```

## 7.5 环境变量

本地后端支持：

- `REMOTE_TRYON_URL`：远程推理 URL，默认 `http://127.0.0.1:9000/tryon`
- `REMOTE_TIMEOUT`：远程请求超时秒数，默认 `300`

## 8. 当前实现的工程特点

优势：

- 结构清晰，职责分离明确。
- 推理服务与业务服务解耦，便于横向扩展。
- 前后端接口简洁，调试成本低。

已知局限：

- 本地和远程接口中存在同步阻塞调用，吞吐能力有限。
- 目前是“单次图像试衣”，不支持摄像头连续帧实时试衣。
- 远程结果文件名存在覆盖风险（并发请求时需改造）。

## 9. 调试与排障建议

## 9.1 快速联通性检查

1. `curl http://127.0.0.1:8000/health`
2. `curl http://127.0.0.1:9000/health`
3. 检查 SSH 隧道是否存活。

## 9.2 常见问题

- 远程不可达：检查 `api_server.py` 进程与隧道端口。
- 首次请求慢：模型懒加载属于正常现象。
- 前端图片不刷新：确认结果 URL 是否带时间戳。

## 10. 版本建议

建议将本项目按语义化版本维护：

- `v1.x`：基础上传试衣。
- `v2.x`：摄像头采集与衣服库选择。
- `v3.x`：实时化与性能优化。

---

本文档用于当前代码基线的技术说明，建议与 `readMe.md` 配合使用：`readMe.md` 侧重运行步骤，本文档侧重设计与实现细节。
