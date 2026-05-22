# 项目进展 · 2026-05-23

> 本次迭代主要解决**工程化部署**与**预设资源体验**两类问题:
>
> - **Git 工程化**:补齐 `.gitignore`,明确"代码 / 项目自带资源 / 运行时数据"三层边界,
>   彻底解决多机部署时 `db.json` 与上传图片导致的 `git pull` 冲突
> - **模特相册功能(核心新增)**:用户/管理员可以预置一批人像照片作为示例模特,
>   在首页直接点选即可作为试穿对象,无需每次都拍照或上传(后端 + 前端 + 后台 + DB 全链路)
> - **示例资源库**:新增 `virtual-tryon/examples/` 目录,内含 41 张衣服 + 29 位模特
>   作为项目自带的演示素材(管理员可从中挑选上传到运行时库)
> - **快捷启动脚本**:Windows 一键启动前后端 + SSH 隧道;Linux GPU 服务器一键启停
>   两个 OOTDiffusion 推理服务
>
> **数据库 schema 已升级到 v2**,老 `db.json` 自动迁移补齐 `models` 字段,**完全向后兼容**。

---

## 目录

- [一、本次迭代总览](#一本次迭代总览)
- [二、Git 工程化:`.gitignore` 与数据边界](#二git-工程化gitignore-与数据边界)
- [三、新增功能 1:模特相册(核心)](#三新增功能-1模特相册核心)
- [四、新增功能 2:示例资源库 `examples/`](#四新增功能-2示例资源库-examples)
- [五、新增功能 3:快捷启动脚本](#五新增功能-3快捷启动脚本)
- [六、其他细节调整](#六其他细节调整)
- [七、API / 数据库变更总览](#七api--数据库变更总览)
- [八、文件级改动清单](#八文件级改动清单)
- [九、如何启动(手动 + 一键)](#九如何启动手动--一键)
- [十、多机协作与 Git 建议](#十多机协作与-git-建议)
- [十一、后续可选优化](#十一后续可选优化)

---

## 一、本次迭代总览

| 改动类别 | 文件数 | 说明 |
|---------|-------|------|
| **后端** | 3 修改 | `storage.py` / `admin.py` / `main.py` 加模特 CRUD |
| **前端 API** | 1 新增 + 1 修改 | `api/models.js` 新增,`api/admin.js` 扩展 5 个函数 |
| **前端组件** | 2 新增 + 1 修改 | `AdminModel{Uploader,sGrid}.vue` 新增,`ClothingDock` 支持自定义标题 |
| **前端视图** | 2 修改 | `HomeView` 加模特 Dock,`AdminView` tab 切换布局 |
| **示例资源** | 70 张图片 | `examples/garment` 41 张 + `examples/model` 29 张 |
| **快捷脚本** | 3 新增 | Windows `.bat` + Linux `.sh × 2` |
| **配置** | 1 修改 | `.gitignore` 全面重写 |

---

## 二、Git 工程化:`.gitignore` 与数据边界

### 2.1 背景问题

项目最初**没有 `.gitignore`**,直接 `git add .` 会把以下东西全部塞进 git:

- `frontend/node_modules/`(61MB,几万文件)
- `backend/.venv/`(Python 虚拟环境,几十 MB)
- `backend/db.json`(业务数据库,会被运行时频繁写入)
- `backend/static/clothes/`(管理员上传的衣服图,运行时数据)
- `backend/static/result_*.jpg`(AI 推理生成的产物,几十 MB)
- `OOTDiffusion/checkpoints/`(模型权重,几 GB,绝对不能进 git)
- 各种 `.DS_Store`、`*.log`、缓存文件等

更严重的:**多机协作时会冲突**。开发机改了源码,部署机的用户上传了新衣服(`db.json` 被服务端写入),`git pull` 时 `db.json` 必然合并冲突。

### 2.2 解决方案 —— 三层数据边界

经过讨论,确立了清晰的数据所有权划分:

| 层 | 内容 | 是否入 git | 理由 |
|---|------|----------|------|
| **代码** | `.py` / `.vue` / `.js` 等源码 | ✅ 入 git | 这是项目本体,所有机器同步 |
| **项目自带资源** | `examples/`、`README.md`、`PROJECT_*.md` | ✅ 入 git | 演示用素材,只读,不会被运行时修改 |
| **运行时数据** | `db.json`、`static/clothes/`、`static/models/`、`static/result_*` | ❌ 忽略 | 各机器独立,代码升级不应覆盖生产数据 |

### 2.3 关键规则(`.gitignore` 节选)

```gitignore
# 业务数据库(运行时,各机器独立)
virtual-tryon/backend/db.json
virtual-tryon/backend/db.json.tmp

# 用户上传 / 生成产物
virtual-tryon/backend/static/clothes/
virtual-tryon/backend/static/models/
virtual-tryon/backend/static/result_*.jpg
virtual-tryon/backend/static/result_*.png
virtual-tryon/backend/static/uploads/

# Python / Node.js 环境
__pycache__/
*.py[cod]
venv/  .venv/  env/
node_modules/
dist/

# AI 模型权重
*.pt  *.pth  *.ckpt  *.safetensors  *.bin
virtual-tryon/OOTDiffusion/checkpoints/**
!virtual-tryon/OOTDiffusion/checkpoints/README.txt

# 系统 / IDE / 日志
.DS_Store  *.swp  .vscode/  .idea/
*.log  logs/
```

> ⚠️ **新机器克隆下来不会报错**:`backend/main.py` 启动时会自动 `mkdir(exist_ok=True)`
> 创建 `static/clothes/` 和 `static/models/`;`storage.py` 也会在 `db.json` 不存在时
> 自动用 `DEFAULT_DB` 创建一个空数据库。

---

## 三、新增功能 1:模特相册(核心)

### 3.1 需求背景

老师希望"点击上传人像时,文件选择器默认打开到示例图片目录"。但是:

> **Web 浏览器的 `<input type="file">` 出于安全考虑,无法指定打开目录**。这是 W3C 硬性
> 规定,所有浏览器(Chrome/Firefox/Safari)都一样,无法绕开。

所以我们做了一个**比"打开目录"更优雅**的方案 —— **预设模特相册**:

- 管理员在后台批量上传若干位"示例模特"
- 用户在首页看到一行模特缩略图,**点击直接载入**到人像槽
- 比"打开文件选择器→翻文件夹→选图→确认"快多了
- 跨系统、跨浏览器、跨设备都通用

### 3.2 设计原则:与衣服 Dock 完全对称

整套模特功能**完整对称**已有的衣服(clothes)功能,只在数据模型上去掉 `category` 字段
(衣服有"上半身/下半身/连衣裙"分类,模特没有)。

| 维度 | 衣服(clothes) | 模特(models) |
|-----|---------------|---------------|
| 数据 ID 前缀 | `c_xxxxxxxxxx` | `m_xxxxxxxxxx` |
| 图片缩放上限 | 长边 800px | 长边 1024px(更保真) |
| 文件存储位置 | `static/clothes/` | `static/models/` |
| 静态访问 URL | `/static/clothes/c_xxx.jpg` | `/static/models/m_xxx.jpg` |
| 公开列表接口 | `GET /api/clothes` | `GET /api/models` |
| 管理 CRUD 接口 | `/api/admin/clothes/*` | `/api/admin/models/*` |
| 分类字段 | `category` ∈ {upperbody,lowerbody,dress} | **(无)** |
| 排序字段 | `order` | `order` |
| 前端 Dock 组件 | `ClothingDock`(复用) | `ClothingDock`(传 `title` props) |
| 后台管理网格 | `AdminClothesGrid` | `AdminModelsGrid`(新建) |
| 后台上传器 | `AdminUploader` | `AdminModelUploader`(新建) |

### 3.3 数据库 Schema 升级(v1 → v2)

`db.json` 升级到 v2,新增 `models` 数组:

```json
{
  "version": 2,
  "clothes": [
    {
      "id": "c_8be2d84943",
      "name": "00006_00",
      "category": "upperbody",
      "filename": "c_8be2d84943.jpg",
      "url": "/static/clothes/c_8be2d84943.jpg",
      "order": 0,
      "created_at": "2026-04-23T06:26:30+00:00"
    }
  ],
  "models": [
    {
      "id": "m_aca5c57b9e",
      "name": "示例模特 1",
      "filename": "m_aca5c57b9e.jpg",
      "url": "/static/models/m_aca5c57b9e.jpg",
      "order": 0,
      "created_at": "2026-05-22T17:19:59+00:00"
    }
  ]
}
```

**完全向后兼容**:`storage._read()` 检测到老版本(无 `models` 字段)会自动补齐
`"models": []`,无需任何人工迁移。

### 3.4 后端实现要点

#### `storage.py` 新增 5 个函数(与衣服对称)

| 函数 | 作用 |
|------|------|
| `list_models() -> List[dict]` | 列出全部模特,按 `(order, created_at)` 排序 |
| `get_model(model_id) -> Optional[dict]` | 按 id 取单个 |
| `gen_model_id() -> str` | 生成 `m_xxx` 前缀的随机 id |
| `add_model(*, id, name, filename, url) -> dict` | 添加,新模特默认放最前(order = min-1) |
| `update_model(model_id, **fields)` | 仅支持改 `name` 和 `order` |
| `reorder_models(ordered_ids) -> int` | 拖拽排序,重写整个列表的 order |
| `delete_model(model_id)` | 删除 db 记录(物理文件由路由层负责删) |

所有写入都走 `threading.RLock` + **原子替换**(写临时文件再 `os.replace`),与衣服模块一致,避免并发写入损坏 `db.json`。

#### `admin.py` 新增 5 条路由(全部需要 Bearer Token)

```
GET     /api/admin/models               # 列表(带 created_at 等完整字段)
POST    /api/admin/models               # 批量上传(multipart, 多文件 + 可选 name)
PATCH   /api/admin/models/{model_id}    # 改名 / 改 order
PUT     /api/admin/models/order         # 批量重排(ids 数组)
DELETE  /api/admin/models/{model_id}    # 删除 (同步移除物理文件)
```

上传逻辑:
1. 校验文件类型(jpg/png/webp/jpg)
2. 用 PIL 转 RGB,缩放到长边 1024px(保留更多细节利于试穿)
3. 用 `m_xxx` 前缀生成新文件名,质量 90 / `optimize=True` 写入 `static/models/`
4. 写入 `db.json`

#### `main.py` 增量

```python
MODELS_DIR = STATIC_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

@app.get("/api/models")
def public_list_models():
    return {"code": 0, "data": storage.list_models()}
```

### 3.5 前端实现要点

#### `ClothingDock.vue` 通用化(向后兼容)

加了两个 props,默认值与原有文案一致,**所有已存在的调用方零改动**:

```vue
const props = defineProps({
  items:       { type: Array, required: true },
  modelValue:  { type: [String, Number], default: null },
  title:       { type: String, default: '服装款式精选' },
  countSuffix: { type: String, default: '款 · 点击试穿' },
})
```

模特 Dock 的调用:

```vue
<ClothingDock
  :items="allModels"
  v-model="selectedModelId"
  title="模特相册"
  count-suffix="位 · 点击使用"
  @update:modelValue="onModelPresetSelect"
/>
```

#### `HomeView.vue` 模特选择逻辑

```js
async function onModelPresetSelect(id) {
  const preset = allModels.value.find(p => p.id === id)
  if (!preset) return
  selectedModelId.value = id
  // ... fetch -> 转 File 对象 -> 同样的 personFile 绑定
  const file = await urlToFile(preset.url, `${preset.id}.jpg`)
  personFile.value = file
}
```

**清空逻辑**:用户重新点击"上传人像"或"拍照"时,自动 `selectedModelId.value = null`,
保证 UI 上"已选模特"高亮不会与"已上传新文件"混淆。

#### `AdminView.vue` Tab 切换布局

后台从"单功能页面"改成 tab 切换:

```
┌─────────────────────────────────────┐
│ [👕 衣服管理] [🧍 模特管理]          │
├─────────────────────────────────────┤
│                                     │
│   (对应 tab 的统计/上传/列表)         │
│                                     │
└─────────────────────────────────────┘
```

两个 tab 各自独立加载、独立刷新、独立显示 toast。

#### `AdminModelUploader.vue` / `AdminModelsGrid.vue`(新建)

- **Uploader**:拖拽 / 点击上传,一次最多 20 张,实时预览,无 category 字段
- **Grid**:网格展示,行内改名 + 拖拽排序 + 二次确认删除,与衣服管理交互一致

### 3.6 全屏 Kiosk 模式策略

**Kiosk(触控全屏)模式保持原状**,不显示模特相册。原因:

- 触控大屏的核心场景是**现场拍照**(已有"点击卡片打开摄像头"交互)
- 底部 Dock 空间宝贵,衣服 Dock 已经占满
- 用户偏好"全屏页面跟之前一样不变"

如果后续要加,推荐做法:在底部加一个紧凑的单行模特横滑条(单卡片约 78×104,
代码思路在 git history 里曾经实现过,可以回头取参考)。

---

## 四、新增功能 2:示例资源库 `examples/`

在项目根的 `virtual-tryon/` 下新增 `examples/` 目录(已入 git):

```
virtual-tryon/examples/
├── garment/      # 41 张示例衣服图片
│   ├── 00055_00.jpg
│   ├── 049949_1.jpg
│   └── ...
└── model/        # 29 张示例模特图片(含 9 张高质量 PNG 模特)
    ├── 01008_00.jpg
    ├── model_1.png
    └── ...
```

**用途**:管理员可以从这些示例图片里挑选,通过后台"上传"功能加入到运行时库
(`static/clothes/` 或 `static/models/`)。

**为什么这个目录入 git**(对比 `static/` 不入 git):
- `examples/` 是项目自带的演示资源,只读,所有部署机器都该有同一份
- `static/` 是运行时数据,各部署独立

总大小 14MB,对 git 来说完全可接受(警戒线一般是单仓库 100MB+)。

---

## 五、新增功能 3:快捷启动脚本

为方便老师演示与日常调试,新增 3 个脚本:

### 5.1 `start_dev.bat`(项目根目录,Windows 端)

**双击即运行**,自动打开 3 个 cmd 窗口:

| 窗口标题 | 内容 |
|---------|------|
| `Backend - uvicorn` | `cd backend && conda activate dev && uvicorn main:app --reload --port 8000` |
| `Frontend - vite` | `cd frontend && npm run dev` |
| `SSH Tunnel - GPU Server` | `ssh -p 3485 -L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001 root@172.24.246.49` |

特点:
- 用 `chcp 65001` 强制 UTF-8,避免中文乱码
- 使用 `%~dp0` 自动取脚本所在目录,**项目放在哪都能跑**
- `start "标题" cmd /k "命令"` 让子窗口保持打开,方便观察日志

### 5.2 `OOTDiffusion/run/start_models.sh`(Linux GPU 服务器)

一键后台启动两个 OOTDiffusion 推理服务:

```bash
cd virtual-tryon/OOTDiffusion/run
./start_models.sh
```

行为:
1. **自动探测 conda 路径**(尝试 `~/anaconda3` / `~/miniconda3` / `/opt/...` / `/root/...` 共 6 个常见位置)
2. 激活 `ootdiffusion` 环境
3. `nohup` 后台启动 HD 模型(端口 9000, upperbody 专用)
4. 等待 3s 让 HD 先抢占显存
5. `nohup` 后台启动 DC 模型(端口 9001, lowerbody/dress)
6. PID 存到 `logs/hd.pid` / `logs/dc.pid`,日志存到 `logs/hd.log` / `logs/dc.log`

**SSH 断开后两个模型继续运行**(`nohup` 的作用)。

**幂等保护**:如果模型已经在跑,脚本会拒绝重复启动并提示先 stop。

### 5.3 `OOTDiffusion/run/stop_models.sh`(Linux GPU 服务器)

```bash
./stop_models.sh
```

行为:
1. 读取 `logs/*.pid`,用 `kill` 优雅终止
2. 等待 5s,如果没退出就 `kill -9` 强杀
3. 如果 PID 文件丢失,自动用 `lsof` 或 `fuser` 从端口 9000/9001 反查进程并停止

### 5.4 ⚠️ 脚本里**可能要根据实际情况修改**的地方

这些是会因环境/网络而变的"硬编码值",换电脑或换 GPU 服务器时检查一遍:

#### Windows 端 `start_dev.bat`

| 行号 | 内容 | 何时需要改 |
|------|------|----------|
| `call conda activate dev` | 后端 conda 环境名 | 如果你的后端 conda 环境名不叫 `dev`(比如改成 `vt-backend`),改这里 |
| `--port 8000` | 后端端口 | 端口冲突时改(同时改前端 `vite.config.js` 里的 proxy 目标) |
| `ssh -p 3485 ... root@172.24.246.49` | SSH 隧道命令 | **最常变**:GPU 服务器换了、端口换了、用户名/IP 变了都要改 |
| `-L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001` | 端口转发映射 | 如果 GPU 服务器上 HD/DC 改了端口,要同步改 |

#### Linux 端 `start_models.sh`

| 段落 | 内容 | 何时需要改 |
|------|------|----------|
| `CONDA_SH` 自动探测列表 | 6 个候选 conda 路径 | 如果你 conda 装在更奇葩的位置(比如 `/data/miniconda3`),把这个路径加到列表里 |
| `conda activate ootdiffusion` | 推理服务 conda 环境名 | 如果环境名不叫 `ootdiffusion`,改这里 |
| `--gpu_id 0` | GPU 编号 | 多卡机器想用其他卡时改 |
| `--port 9000` / `--port 9001` | HD / DC 端口 | 端口冲突时改(同时改后端 `main.py` 里的 `REMOTE_TRYON_URL_HD/DC` 和 SSH 隧道命令) |
| `--n_samples 4 --scale 2.0` | 推理参数 | 调质量/速度时改 |

> 💡 **建议**:把这些可变值集中到一个 `.env` 文件,脚本里 `source .env` 读取。
> 但当前规模(就一台 Windows + 一台 GPU)直接硬编码也够用,后续真有多套部署再做。

#### 后端 `main.py`(脚本未涉及,但会一起变)

```python
REMOTE_TRYON_URL_HD = "http://127.0.0.1:9000/tryon"   # 改端口要同步
REMOTE_TRYON_URL_DC = "http://127.0.0.1:9001/tryon"   # 改端口要同步
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # 生产环境一定要改
```

---

## 六、其他细节调整

### 6.1 `HomeView.vue` 页脚版权

```diff
- Powered by OOTDiffusion · © 2026 Virtual Try-On
+ 西安工程大学 · 计算机科学学院 · Virtual Try-On System
```

### 6.2 `AdminView.vue` 副标题

```diff
- 虚拟试衣 · 衣服库管理
+ 虚拟试衣 · 资源库管理
```

(因为现在管的不只是衣服,还有模特)

---

## 七、API / 数据库变更总览

### 7.1 数据库

| 项 | v1(旧) | v2(新) |
|---|---------|---------|
| `version` 字段 | `1` | `2` |
| `clothes` 数组 | ✅ | ✅ 保持不变 |
| `models` 数组 | ❌ | ✅ 新增 |
| 老 db.json 兼容 | — | ✅ 自动迁移补齐 |

### 7.2 后端 API(新增 6 个)

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/models` | 公开 | 模特列表(前台 Dock) |
| GET | `/api/admin/models` | Bearer | 模特列表(后台) |
| POST | `/api/admin/models` | Bearer | 批量上传(multipart) |
| PATCH | `/api/admin/models/{id}` | Bearer | 改名 / 改 order |
| PUT | `/api/admin/models/order` | Bearer | 批量重排 |
| DELETE | `/api/admin/models/{id}` | Bearer | 删除 + 移除物理文件 |

**老接口零改动**,所有 `/api/clothes`、`/api/admin/clothes/*`、`/api/tryon`、`/health`、`/api/admin/login` 等行为完全一致。

### 7.3 前端 API 客户端(`api/admin.js` 新增 5 个函数)

```js
adminListModels()
uploadModels(files, { name })
patchModel(id, fields)
reorderModels(ids)
deleteModel(id)
```

新建 `api/models.js`:

```js
listModels()       // 公开拉取模特列表
```

---

## 八、文件级改动清单

### 8.1 新增文件(9 个)

```
.gitignore                                                   # 新增
start_dev.bat                                                # Windows 一键启动
virtual-tryon/CHANGELOG_2026-05-23.md                        # 本文档
virtual-tryon/examples/garment/  (41 张图)                    # 示例衣服
virtual-tryon/examples/model/    (29 张图)                    # 示例模特
virtual-tryon/OOTDiffusion/run/start_models.sh               # Linux 启动
virtual-tryon/OOTDiffusion/run/stop_models.sh                # Linux 停止
virtual-tryon/frontend/src/api/models.js                     # 模特公开 API
virtual-tryon/frontend/src/components/AdminModelUploader.vue # 后台模特上传
virtual-tryon/frontend/src/components/AdminModelsGrid.vue    # 后台模特网格
```

### 8.2 修改文件(8 个)

```
virtual-tryon/backend/storage.py                # +97 行(models CRUD)
virtual-tryon/backend/admin.py                  # +92 行(/admin/models 5 个路由)
virtual-tryon/backend/main.py                   # +8 行(/api/models + MODELS_DIR)
virtual-tryon/frontend/src/api/admin.js         # +31 行(模特管理函数)
virtual-tryon/frontend/src/components/ClothingDock.vue   # 加 title/countSuffix props
virtual-tryon/frontend/src/views/HomeView.vue            # 加模特 Dock + 页脚
virtual-tryon/frontend/src/views/AdminView.vue           # tab 切换布局
virtual-tryon/frontend/src/views/KioskView.vue           # 暂未改动(原计划改后回滚)
```

---

## 九、如何启动(手动 + 一键)

### 9.1 一键启动(推荐,适合常规演示)

#### Windows 服务器

把整个项目同步到 Windows 服务器,**双击 `start_dev.bat`**。
会自动开 3 个 cmd 窗口:
- Backend(端口 8000)
- Frontend(Vite,通常 5173)
- SSH 隧道(把 GPU 服务器的 9000/9001 映射到本地)

第一次启动会问 SSH 密码 / fingerprint,正常输入即可。

#### Linux GPU 服务器

```bash
cd 项目目录/virtual-tryon/OOTDiffusion/run
./start_models.sh    # 启动 HD + DC 两个推理服务
tail -f logs/hd.log  # 观察启动进度(看到 'Uvicorn running on ...' 就 OK)
```

停止:

```bash
./stop_models.sh
```

### 9.2 手动启动(适合开发调试 / 排错)

#### Windows 服务器

```bash
# 终端 1 —— 后端
cd virtual-tryon/backend
conda activate dev
uvicorn main:app --reload --port 8000

# 终端 2 —— 前端
cd virtual-tryon/frontend
npm install     # 仅第一次需要
npm run dev

# 终端 3 —— SSH 隧道
ssh -p 3485 -L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001 root@172.24.246.49
```

#### Linux GPU 服务器

```bash
# 终端 1 —— HD 模型(upperbody 专用)
cd virtual-tryon/OOTDiffusion/run
conda activate ootdiffusion
python api_server.py --gpu_id 0 --port 9000 --model_type hd --n_samples 4 --scale 2.0

# 终端 2 —— DC 模型(lowerbody / dress)
cd virtual-tryon/OOTDiffusion/run
conda activate ootdiffusion
python api_server.py --gpu_id 0 --port 9001 --model_type dc --n_samples 4 --scale 2.0
```

### 9.3 启动顺序建议

理想顺序:**Linux GPU 模型先启动 → Windows SSH 隧道 → Windows 后端 → Windows 前端**。

GPU 模型加载需要 30s ~ 2min,如果前端先起来用户点了"开始试衣",会因为后端连不上远程
推理服务而 502。所以脚本里我特意让 SSH 隧道窗口放最后启,**给用户一个心理预期**。

### 9.4 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| 前台 | http://localhost:5173 | 用户试衣页面 |
| 后台登录 | http://localhost:5173/admin/login | 默认密码 `admin123`(改 `.env` 或 `admin.py`) |
| 触控全屏 | http://localhost:5173/kiosk | 65 寸大屏专用 |
| 后端健康检查 | http://localhost:8000/health | 检查后端 + 两个远程推理服务是否可达 |

---

## 十、多机协作与 Git 建议

### 10.1 现在的目录边界

```
项目根/
├── .gitignore              ✅ git 追踪
├── start_dev.bat           ✅ git 追踪
├── virtual-tryon/
│   ├── backend/
│   │   ├── *.py            ✅ 代码,git 追踪
│   │   ├── db.json         ❌ 运行时数据,各机器独立
│   │   ├── .venv/          ❌ 虚拟环境
│   │   └── static/
│   │       ├── clothes/    ❌ 运行时上传,各机器独立
│   │       ├── models/     ❌ 运行时上传,各机器独立
│   │       └── result_*.jpg ❌ AI 推理产物
│   ├── frontend/
│   │   ├── src/            ✅ 代码,git 追踪
│   │   ├── node_modules/   ❌ npm 装的依赖
│   │   └── dist/           ❌ 构建产物
│   ├── examples/           ✅ 项目自带演示资源,git 追踪
│   └── OOTDiffusion/
│       ├── run/
│       │   ├── *.py        ✅ 代码
│       │   ├── *.sh        ✅ 启停脚本
│       │   └── logs/       ❌ 推理日志
│       └── checkpoints/    ❌ 模型权重(几 GB,不能进 git)
```

### 10.2 多机协作工作流

#### 场景 A:开发机改代码 → 部署机拉取

```bash
# 开发机
git add .
git commit -m "feat: ..."
git push

# 部署机(Windows 服务器)
git pull   # ✅ 只更新代码,db.json 和 static/* 完全不动
# 重启后端 + 前端(start_dev.bat)
```

> **永远不会因为衣服/模特/推理结果而冲突**,因为这些都不在 git 里。

#### 场景 B:换台新机器部署

```bash
git clone <repo>
cd virtual-try-on-system/virtual-tryon

# 后端
cd backend
conda create -n dev python=3.10
conda activate dev
pip install -r requirements.txt

# 前端
cd ../frontend
npm install

# 启动(此时 db.json 不存在,首次启动会自动创建空数据库)
# 进入后台 /admin → 上传几件衣服 + 几位模特 → 完成初始化
```

### 10.3 部署生产环境前必做

- [ ] 修改 `admin.py` 里的 `ADMIN_PASSWORD`(或设置 `ADMIN_PASSWORD` 环境变量)
- [ ] 检查 `main.py` 里的 `CORSMiddleware` 的 `allow_origins`(目前只允许 localhost:5173)
- [ ] 检查 `REMOTE_TRYON_URL_HD/DC` 是否匹配实际部署
- [ ] 检查 `start_dev.bat` 里的 SSH 命令是否匹配新环境

---

## 十一、后续可选优化

按优先级排序:

1. **配置文件外置**:把 SSH 目标地址、conda 环境名、端口等常变项抽取到 `.env` 或
   `config.ini`,脚本和后端共读,避免散落各处。

2. **生产部署文档**:补一份 `DEPLOYMENT.md`,涵盖 Nginx 反代、SSL、
   守护进程(`systemd` / `pm2` / Windows 服务)等。

3. **Kiosk 模式加模特相册**(如老师要求):在底部 Dock 上方加一行紧凑的模特横滑条,
   78×104 卡片大小,触控屏友好。代码思路本次曾实现过,可从 git history 取参考。

4. **批量从 `examples/` 一键导入**:后台增加按钮"从 examples/garment 批量导入",
   省得管理员手动一张一张选。

5. **试穿历史 / 收藏夹**:用户的 `result_*.jpg` 现在只是堆在 `static/` 里,
   可以加个 SQLite 或扩展 `db.json` 记录"哪个用户试过哪件衣服 + 哪位模特",
   做成"我的试衣记录"功能。

6. **替换 OOTDiffusion 为更新的模型**:`PROJECT_FUTURE_ROADMAP.md` 里已经讨论过,
   可考虑 IDM-VTON / CatVTON / Leffa 等新模型,统一接入 `/api/tryon` 接口即可。

---

> **本次迭代 Commit 历史**
>
> ```
> ac7d72d  新增模特相册资源库功能(前后端 + 后台管理)
> 965c46f  添加示例资源库与页脚版权信息
> 739d211  完成虚拟试衣系统基础功能搭建
> ```
>
> 当前工作区还有未提交的"Kiosk 回滚 + 启动脚本"改动,提交建议见对话历史。
