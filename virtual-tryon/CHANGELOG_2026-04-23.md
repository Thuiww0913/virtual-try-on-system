# 项目进展 · 2026-04-23

> 这是一次相当大的迭代。从一个"能跑但简陋"的原型，升级为具备：
> - 现代化用户端界面（Midjourney / Apple 风格）
> - 后台管理系统（管理员可批量上传、编辑、排序衣服素材）
> - 服装类别智能识别（解决"裤子穿到上半身"的硬伤）
> - HD / DC 双模型按类别自动路由（保证画质）
> - 跨平台一致的 UI 显示
>
> 的完整 AI 虚拟试衣 Web 应用。

---

## 目录

- [一、本次迭代总览](#一本次迭代总览)
- [二、用户端 UI 全面重构](#二用户端-ui-全面重构)
- [三、后台管理系统（全新）](#三后台管理系统全新)
- [四、服装类别打通（修复"裤子穿上身"Bug）](#四服装类别打通修复裤子穿上身bug)
- [五、HD / DC 双模型路由（提升画质）](#五hd--dc-双模型路由提升画质)
- [六、跨平台 UI 一致性 + 视觉精修](#六跨平台-ui-一致性--视觉精修)
- [七、文件级改动清单](#七文件级改动清单)
- [八、如何启动（完整流程）](#八如何启动完整流程)
- [九、常见问题与排查](#九常见问题与排查)
- [十、后续可选优化](#十后续可选优化)
- [附：项目结构](#附项目结构)

---

## 一、本次迭代总览

| 模块 | 改动类型 | 说明 |
|---|---|---|
| 用户端 UI | **整体重构** | 从单页平铺布局升级为"上传 → 选择 → 生成 → 查看"的卡片式工作流，加入 Dock 选衣、进度条、模态放大、动效 |
| 后台管理 | **全新模块** | 新增 `/admin` 路由 + 登录鉴权 + 批量上传 + 行内编辑 + 拖拽排序 + 删除 |
| 数据存储 | 重写 | 衣服列表从前端硬编码迁移到后端 JSON 持久化，原子写 + 线程锁 |
| 推理路由 | **新增能力** | 按服装类别（上半身 / 下半身 / 连衣裙）分别路由到 HD / DC 模型 |
| 类别系统 | 修复+对齐 | 与 OOTDiffusion 官方一致：`upperbody=0 / lowerbody=1 / dress=2`，端到端透传 |
| 跨平台兼容 | 修复 | Mac 角标遮挡标题、Linux 字体 fallback 缺失、Dock 悬浮裁剪 |
| Python 版本 | 修复 | 兼容 Python 3.9（`X | None` 改 `Optional[X]`） |

---

## 二、用户端 UI 全面重构

### 设计目标

参照 Midjourney / OpenAI / Apple 的克制美学，做到：

1. **简洁高级**：深色背景 + 一处亮绿主色 + 微弱网格底纹
2. **操作路径清晰**：左 → 中 → 右 三栏对应"人 → 衣 → 结果"的视觉流
3. **视觉集中**：核心三件事在一屏内完成
4. **细节动效**：hover 放大、按钮反馈、淡入、扫描线、shimmer

### 1) 顶部标题

- 中文主标题「虚拟试衣」+ 英文副标 `Virtual Try-On`
- 左侧 logo（绿色衣架图标 + glow 阴影）
- 右侧两个胶囊按钮：
  - `AI Powered · OOTDiffusion`（带脉冲指示灯）
  - 「后台」入口（跳转 `/admin`）

### 2) 三栏卡片（核心工作区）

| 1️⃣ 人物图片 | 2️⃣ 服装款式 | 3️⃣ 试穿结果 |
|---|---|---|
| 上传 / 拖拽 | 上传 / 从 Dock 选 | 加载动画 / 放大 / 下载 |

- 统一 `aspect-[3/4]`、圆角 `rounded-3xl`、`shadow-card` + hover 上浮
- 空态：图标 + 文案 + 渐变虚线边框
- 拖拽进入时变绿 + scale + glow
- 加载态：skeleton + shimmer + 扫描线 + 旋转 spinner + 文案
- 已上传：hover 出现「更换 / 放大 / 下载」三个按钮
- 序号徽章：内联在标题左侧（解决跨平台遮挡问题，详见第六节）

### 3) 衣服 Dock（Mac 风格）

底部一行横向滚动的"衣服坞"，主要特性：

- 鼠标悬停时按距离平滑放大（最大 1.22x，`easeOutCubic`）
- 鼠标移出立即还原
- 左右按钮 + 鼠标滚轮横滚 + 触摸滑动
- 选中态：绿色外描边 + 右上角勾选小圆
- 两侧 `mask-image` 渐隐
- 项目少（≤6）时自动居中
- **充足 padding-top 防止悬浮放大被裁剪**（详见第六节）

### 4) 分类筛选

Dock 上方一排胶囊式分类：`全部 / 上半身 / 下半身 / 连衣裙`，点击即过滤。

### 5) 服装类别选择器（新增）

选完衣服后，CTA 上方会出现一组 chips，可手动指定即将送入推理的类别。预设衣服会自动同步类别（带"来自预设"小提示）。

### 6) CTA 与进度反馈

- 主按钮"开始试衣"：满足条件时绿色发光 + 缩放反馈，否则灰态禁用
- Loading 中：科技感渐变进度条 + shimmer + 阶段文案（"上传图像 → 解析人体姿态 → 提取服装特征 → 扩散模型推理 → 合成最终图像"）
- 错误态：红色描边 toast，带图标

### 7) 结果模态

点击结果卡片放大，全屏 modal + 半透明遮罩 + 居中显示，附带下载按钮。

### 8) 全局视觉

- 深色 `#07080b` 底色
- 顶部右上 / 底部左下两个 radial gradient 装饰球（绿 + 蓝）
- 弱化网格背景（`bg-grid` + 径向 mask 让边缘自然消失）
- 自定义 Tailwind 主题：`accent` 主色、`shadow-card` / `shadow-accent-glow` 阴影、`fade-up / shimmer / scan / pulse-soft` 动画
- Google Fonts：`Inter` + `Space Grotesk`，加上完整中文回退

---

## 三、后台管理系统（全新）

为了让管理员能像运营商品一样维护衣服库，新增了完整的后台模块。

### 后端 (`backend/admin.py`)

- 路由前缀：`/admin/api/*`
- **登录**：`POST /admin/api/login`，密码校验通过后下发 Token
- **列表 / 创建 / 更新 / 删除**：`GET / POST / PUT / DELETE /admin/api/clothes/...`
- **批量上传**：`POST /admin/api/upload`，多文件 + 默认分类
- **排序**：`POST /admin/api/clothes/reorder`，接收 ID 数组直接落库
- **鉴权**：除 `/login` 外的所有路由通过 `Depends(verify_token)` 校验 Bearer Token

### 数据存储 (`backend/storage.py`)

- 简单 JSON 文件 `db.json`，避免引入 SQLite/Redis 这类基础设施
- **原子写**：先写临时文件再 `os.replace`，杜绝半写状态
- **线程锁**：`threading.Lock()` 保护并发写
- 提供 `add_cloth / update_cloth / delete_cloth / reorder_clothes / list_clothes` 等高层 API
- 类别白名单：`{upperbody, lowerbody, dress}`，越界自动 fallback 到 `DEFAULT_CATEGORY`

### 图片处理

- 上传时统一用 PIL 处理：转 RGB → JPEG（质量 92） → 限定最大边长 1024px
- 文件名用 `uuid` 防冲突，落到 `static/clothes/<uuid>.jpg`
- 提供 `url`（完整可访问路径）+ `thumb`（同 url，预留缩略图扩展位）

### 前端 (`frontend/src/views/AdminView.vue` 等)

| 组件 | 作用 |
|---|---|
| `AdminLoginView.vue` | 登录页，输入密码获取 token，存入 `localStorage` |
| `AdminView.vue` | 后台主页，包含上传区 + 衣服管理网格 |
| `AdminUploader.vue` | 批量上传：拖拽 / 点击选择多文件 + 分类 picker + 进度提示 |
| `AdminClothesGrid.vue` | 卡片网格：行内编辑名称/分类、HTML5 拖拽排序、删除确认 |
| `api/admin.js` | 后台专用接口封装 |
| `api/client.js` | axios 实例，统一注入 Bearer Token + 401 自动跳登录 |
| `router/index.js` | 路由 + `beforeEach` 鉴权守卫，未登录跳 `/admin/login` |

### 安全提示

- 默认管理员密码硬编码在 `backend/admin.py` 顶部，**生产前务必修改**
- 当前 token 是无过期时间的简单字符串，后续可升级为 JWT + 过期时间
- 没有 CSRF 防护，仅适合内网 / 单人使用

---

## 四、服装类别打通（修复"裤子穿上身"Bug）

### 现象

用户反馈：上传一条裤子，结果生成图里裤子被穿到了上半身位置。

### 根因

OOTDiffusion 远程推理服务约定：

```
category = 0 → upperbody (上半身)
category = 1 → lowerbody (下半身)
category = 2 → dress     (连衣裙)
```

而本地后端在调用远程时**没传 `category` 参数**，远程默认 0（upperbody），所以无论你传什么衣服都按上半身处理。

### 修复（端到端，全链路）

| 层 | 改动 |
|---|---|
| `backend/storage.py` | 类别集合规范成 `{upperbody, lowerbody, dress}`；新增 `CATEGORY_TO_INT` 映射 |
| `backend/main.py` | `/api/tryon` 新增 `category` 表单字段，校验 → 转 int → 透传到远程 `data={"category": str(cat_int)}` |
| `frontend/src/api/clothes.js` | 三种分类常量 + `DEFAULT_CATEGORY = 'upperbody'` |
| `frontend/src/views/HomeView.vue` | 衣服区下方动态显示「服装类别」选择器；选预设时自动同步类别；提交时附带 |
| `frontend/src/components/AdminUploader.vue` | 后台上传默认分类对齐为 `upperbody` |

### 重要前提

要让 `lowerbody` / `dress` 真正生效，远程 `api_server.py` **必须用 `--model_type dc` 启动**，默认的 `hd` 模型只支持上半身。

---

## 五、HD / DC 双模型路由（提升画质）

### 背景

用户从 `--model_type hd` 切到 `--model_type dc --n_samples 1` 后画质明显下降。

### 根因

| 模型 | 训练集 | 支持类别 | 上半身画质 |
|---|---|---|---|
| `hd` | VITON-HD | 仅 upperbody | **最佳** |
| `dc` | DressCode | upperbody / lowerbody / dress | 通用但略差 |

外加 `--n_samples 1` 砍掉了"4 选 1"的随机过滤机制。

### 修复

本地 backend 同时连接 **两个远程推理服务**，按 category 自动路由：

```python
# backend/main.py
REMOTE_TRYON_URL_HD = "http://127.0.0.1:9000/tryon"   # upperbody → HD
REMOTE_TRYON_URL_DC = "http://127.0.0.1:9001/tryon"   # lowerbody / dress → DC

def pick_remote_url(category: str) -> str:
    if category == "upperbody":
        return REMOTE_TRYON_URL_HD
    return REMOTE_TRYON_URL_DC
```

### `/health` 接口同步升级

现在能同时上报两个远程服务的健康状态：

```json
{
  "backend": "ok",
  "remote_hd": { "url": "http://127.0.0.1:9000/tryon", "status": "ok",          "detail": "ready" },
  "remote_dc": { "url": "http://127.0.0.1:9001/tryon", "status": "unreachable", "detail": "Connection refused" }
}
```

### 显存不够想退化为单服务？

把两个常量填一样的就行，逻辑零改动：

```python
REMOTE_TRYON_URL_HD = "http://127.0.0.1:9001/tryon"   # 都指向 DC
REMOTE_TRYON_URL_DC = "http://127.0.0.1:9001/tryon"
```

---

## 六、跨平台 UI 一致性 + 视觉精修

用户反馈 Mac 和 Linux 上同一页面渲染差异很大，逐项修复：

### 问题 A：Mac 上「人物图片」被截成「物图片」

**根因**：序号徽章用了 `absolute -top-3 -left-3` 浮在卡片左上角外，与上方标签行在 Z 轴上"擦肩而过"，Mac 字体宽度不同时正好压住了首字符。

**修复**：徽章 **内联** 到标签行（`flex-shrink-0` 的小圆点），与文字水平排列，永不重叠。

### 问题 B：Dock 悬浮放大被容器裁剪

**根因**：CSS 规范规定 `overflow-x: auto` 会**强制** `overflow-y: auto`，即使写 `overflow-y: visible` 也会被忽略。

**修复（4 招组合拳）**：

1. scroller 留 **40px 上方 padding**，预留放大空间
2. `MAX_SCALE` 从 1.35 → **1.22**，加 `easeOutCubic` 缓动
3. 用 `mask-image` 实现两侧渐隐遮罩（替换原绝对定位的遮罩 div，避免 z-index 打架）
4. 衣服数 ≤ 6 时自动 `justify-center`

### 问题 C：跨平台字体 fallback 缺失

**修复**：在 `style.css` 加入完整的中文字体栈：

```
'Inter' / 'DM Sans'
  → 'PingFang SC' (macOS)
  → 'Microsoft YaHei' (Windows)
  → 'Noto Sans CJK SC' / 'WenQuanYi Micro Hei' (Linux)
```

并启用 `text-rendering: optimizeLegibility` + `font-feature-settings`，三个系统字宽 / 行高基本对齐。

### 顺手的视觉清理

- 去掉了三个卡片之间的"连接箭头"，更克制
- 三栏改为等宽 `grid-cols-3 gap-5`
- Dock 标题压缩为单行：`服装款式精选 · N 款 · 点击试穿`
- 标题区固定 `h-7` 三栏对齐

---

## 七、文件级改动清单

### 后端 (`virtual-tryon/backend/`)

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `main.py` | **重写** | 加入 HD/DC 双 URL 配置和路由函数；`/api/tryon` 新增 `category` 参数；`/health` 升级为双服务检测；Python 3.9 类型注解兼容 |
| `storage.py` | **新增** | JSON 持久化 + 原子写 + 线程锁；分类规范化（upperbody/lowerbody/dress）+ int 映射 |
| `admin.py` | **新增** | 后台 API 全套：login / list / create / update / delete / upload / reorder + Bearer Token 鉴权 |
| `requirements.txt` | 已有 | 新增依赖 `python-multipart`（上传必备） |

### 前端 (`virtual-tryon/frontend/`)

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `index.html` | 调整 | 标题改中文；引入 Inter + Space Grotesk 字体 |
| `tailwind.config.js` | 扩展 | 自定义 ink/accent/cyan 调色板；shadow-card / shadow-accent-glow 阴影；fade-up / shimmer / scan / pulse-soft 动画 |
| `src/style.css` | 扩展 | 全局深色底；网格背景；scrollbar；进度条渐变；中文字体栈 |
| `src/main.js` | 调整 | 引入 vue-router |
| `src/router/index.js` | **新增** | 路由配置 + 鉴权守卫 |
| `src/App.vue` | **重写** | 改为简单的 router-view 外壳 |
| `src/views/HomeView.vue` | **新增** | 用户端主页（原 App.vue 主体，+ 类别选择器、Dock、CTA、进度、错误、模态） |
| `src/views/AdminLoginView.vue` | **新增** | 管理员登录页 |
| `src/views/AdminView.vue` | **新增** | 后台主页（上传区 + 管理网格） |
| `src/components/ImageSlot.vue` | **新增 + 重构** | 三栏卡片通用组件；序号徽章改内联（跨平台一致） |
| `src/components/ProgressBar.vue` | **新增** | 科技感渐变进度条 + shimmer + floating dot |
| `src/components/ClothingDock.vue` | **新增 + 重构** | Mac 风格 Dock；MAX_SCALE/缓动/mask-image/居中等优化 |
| `src/components/ResultModal.vue` | **新增** | 结果全屏模态 |
| `src/components/AdminUploader.vue` | **新增** | 批量上传 + 分类选择 + 进度 |
| `src/components/AdminClothesGrid.vue` | **新增** | 卡片网格 + 行内编辑 + 拖拽排序 + 删除 |
| `src/api/client.js` | **新增** | axios 实例 + Token 注入 + 401 自动跳登录 |
| `src/api/clothes.js` | **新增** | 公开衣服列表接口 + 分类常量 |
| `src/api/admin.js` | **新增** | 后台专用接口封装 |
| `src/data/clothes.js` | **删除** | 数据已迁移到后端 |

---

## 八、如何启动（完整流程）

### 前置条件

- 远程 GPU 服务器：装好 OOTDiffusion，能跑通 `python api_server.py`（显存推荐 ≥ 16GB）
- 本地：Python 3.9+、Node.js 18+、SSH 客户端

### 步骤 1：远程启动两个推理服务

> 在远程服务器的 `OOTDiffusion/run/` 目录下执行：

```bash
# 终端 1 — HD 服务（上半身专用，效果最好）
python api_server.py \
  --gpu_id 0 \
  --port 9000 \
  --model_type hd \
  --n_samples 4 \
  --scale 2.0

# 终端 2 — DC 服务（下半身 / 连衣裙）
python api_server.py \
  --gpu_id 0 \
  --port 9001 \
  --model_type dc \
  --n_samples 4 \
  --scale 2.0
```

> 显存说明：单服务峰值约 8~14GB。一张卡跑两个建议至少 24GB；不够就只跑 DC，把 backend 里两个 URL 都指向 DC 端口即可。`--n_samples 1` 显存最省但画质明显下降，**不推荐**。

### 步骤 2：本地建立 SSH 端口映射

```bash
ssh -L 9000:127.0.0.1:9000 \
    -L 9001:127.0.0.1:9001 \
    user@your-gpu-server
```

> 一条命令同时映射两个端口，本地 backend 才能像调本地服务一样调远程推理。

### 步骤 3：启动本地后端

```bash
cd virtual-tryon/backend

# 首次：创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 启动
uvicorn main:app --reload --port 8000
```

启动成功的日志：

```
[INFO] Remote tryon URL (HD, upperbody)        : http://127.0.0.1:9000/tryon
[INFO] Remote tryon URL (DC, lowerbody/dress)  : http://127.0.0.1:9001/tryon
[INFO] Remote timeout                          : 300s
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 步骤 4：启动前端

```bash
cd virtual-tryon/frontend

# 首次：安装依赖
npm install

# 开发模式
npm run dev
# 浏览器打开 http://localhost:5173
```

### 步骤 5：登录后台，上传衣服素材

1. 浏览器访问 `http://localhost:5173/admin/login`
2. 默认密码见 `backend/admin.py` 顶部 `ADMIN_PASSWORD`（默认 `admin123`，**生产前务必改掉**）
3. 登录后：
   - 上方"批量上传"区域：拖拽多张图片 + 选择分类 → 上传
   - 下方"衣服管理"网格：双击改名、下拉改分类、拖拽排序、删除
4. 上传的衣服会立即在前台 Dock 出现

### 步骤 6：开始试衣

1. 回到 `http://localhost:5173/`
2. **左卡**：上传一张人像（正面站立效果最佳）
3. **中卡**：从底部 Dock 选衣服 / 或直接上传一张
4. CTA 上方确认「服装类别」选择正确
5. 点击「开始试衣」，等待 30~120 秒
6. 结果出来后可点击放大、下载

### 步骤 7（可选）：健康检查

```bash
curl http://127.0.0.1:8000/health
```

正常返回：

```json
{
  "backend": "ok",
  "remote_hd": { "url": "http://127.0.0.1:9000/tryon", "status": "ok", "detail": "ready" },
  "remote_dc": { "url": "http://127.0.0.1:9001/tryon", "status": "ok", "detail": "ready" }
}
```

---

## 九、常见问题与排查

### Q1：`uvicorn` 启动报 `Address already in use`

```bash
# 查看占用 8000 端口的进程
lsof -ti :8000 | xargs kill -9

# 或者换端口
uvicorn main:app --reload --port 8001
# 别忘了改 frontend/vite.config.js 里的代理目标
```

### Q2：Python 3.9 报 `unsupported operand type(s) for |: 'type' and 'NoneType'`

已在 `storage.py / main.py` 中把 `X | None` 改为 `Optional[X]`、`list[dict]` 改为 `List[dict]`。如果你新加代码遇到同样报错，记得 `from typing import Optional, List, Dict, Any`。

### Q3：后台上传报 `Form data requires "python-multipart" to be installed`

```bash
pip install python-multipart
```

或直接 `pip install -r requirements.txt`。

### Q4：远程返回正常但画质很糟

- `/health` 看两个服务都是 `ok` 吗？
- 上半身请求是否真的走了 HD？看 backend 日志：`Forwarding to remote (upperbody): http://127.0.0.1:9000/tryon`
- 远程 `--n_samples` 设置 ≥ 2，1 张图随机性太大

### Q5：上传衣服后前台不显示

- 检查 `backend/db.json` 是否写入成功
- 检查 `backend/static/clothes/` 目录下是否有文件
- 浏览器强制刷新（Ctrl+Shift+R）清除缓存

### Q6：分类不匹配（旧数据残留）

如果是从老版本升级过来，`db.json` 可能还存着旧的 `top / bottom / other` 分类：

```bash
cd virtual-tryon/backend
rm db.json
rm -rf static/clothes/*
# 重启 backend，从后台重新上传
```

### Q7：Mac 上字体看起来还是不一样

- 浏览器 F12 → Network 看 Inter / DM Sans 是否成功从 Google Fonts 加载（被墙就 fallback 到 PingFang SC）
- 也可以本地下载 woff2 自托管，避免 Google Fonts 超时

### Q8：Dock 上的衣服点击没反应

通常是 `selectedPresetId` 状态错乱。F12 console 看是否有报错；最稳妥的办法是刷新页面。

---

## 十、后续可选优化

| 优先级 | 项目 | 说明 |
|---|---|---|
| 高 | **任务队列** | 当前 `/api/tryon` 是同步调用，多用户同时试穿会排队卡死。引入 Redis + Celery 改成异步任务 + 轮询 |
| 高 | **结果缓存** | 同一组（人像 hash + 衣服 hash + 类别）只跑一次，其余直接命中缓存 |
| 高 | **JWT + 密码哈希** | 当前后台 token 是无过期的简单字符串，密码明文比对，建议升级为 JWT + bcrypt |
| 中 | **历史记录** | 每个会话保存最近 N 次试穿结果，支持回看 |
| 中 | **WebSocket 进度推送** | 替换前端 mock 进度条，让真实进度同步显示 |
| 中 | **多管理员系统** | 当前是单密码，扩展为多用户 + 权限分级 |
| 中 | **缩略图生成** | 后台上传时同时生成 200x200 缩略图，Dock 加载更快 |
| 低 | **图片质量评分** | 用 CLIP 之类对生成图打分，不达标时自动重跑 |
| 低 | **A/B 对比入口** | 同时跑 HD 和 DC 两个结果让用户对比选择 |
| 低 | **CDN / 对象存储** | `static/` 目录上 OSS / S3，减轻本地磁盘压力 |
| 低 | **响应式适配** | 当前主要针对桌面端优化，移动端 < 640px 还可以再打磨 |

---

## 附：项目结构

```
virtual-tryon/
├── backend/
│   ├── main.py                # FastAPI 入口；/api/tryon、/api/clothes、/health
│   ├── admin.py               # 后台管理 API（登录 / 上传 / CRUD / 排序）
│   ├── storage.py             # 衣服库 JSON 存储 + 原子写 + 分类映射
│   ├── requirements.txt
│   ├── db.json                # 衣服元数据（自动生成）
│   └── static/
│       ├── clothes/           # 衣服图片
│       └── result_*.jpg       # 生成结果
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── HomeView.vue          # 用户端主页
│   │   │   ├── AdminLoginView.vue    # 管理员登录
│   │   │   └── AdminView.vue         # 后台管理主页
│   │   ├── components/
│   │   │   ├── ImageSlot.vue         # 三栏卡片（人/衣/果）
│   │   │   ├── ClothingDock.vue      # 底部 Mac 风格 Dock
│   │   │   ├── ProgressBar.vue       # 进度条
│   │   │   ├── ResultModal.vue       # 结果模态
│   │   │   ├── AdminUploader.vue     # 后台批量上传
│   │   │   └── AdminClothesGrid.vue  # 后台衣服管理网格
│   │   ├── api/
│   │   │   ├── client.js             # axios 实例（注入 token、401 处理）
│   │   │   ├── clothes.js            # 公开衣服列表 + 分类常量
│   │   │   └── admin.js              # 后台专用接口
│   │   ├── router/
│   │   │   └── index.js              # 路由 + 鉴权 guard
│   │   ├── style.css                 # 全局样式 + 中文字体栈
│   │   ├── App.vue                   # router-view 外壳
│   │   └── main.js
│   ├── tailwind.config.js            # 自定义色 / 阴影 / 动画
│   ├── vite.config.js                # /api 代理到 :8000
│   ├── index.html
│   └── package.json
│
├── OOTDiffusion/                     # 推理模型仓库（远程使用）
│   └── run/
│       └── api_server.py             # 推理服务，需用 --model_type hd/dc 启动
│
├── PROJECT_DOCUMENTATION.md          # 旧版项目文档
├── PROJECT_FUTURE_ROADMAP.md         # 旧版路线图
├── CHANGELOG_2026-04-23.md           # ← 本文档
└── readMe.md
```

---

**今日辛苦了，先休息一下，下个迭代见。**
