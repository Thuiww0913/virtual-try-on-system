# 项目进展 · 2026-05-15

> 本次迭代主要围绕**触控大屏展示场景**展开。从一个"在桌面端可用"的 Web 应用，
> 升级为同时支持桌面 + 65 寸 4K 触控屏（3840×2160）的双形态应用：
>
> - 用户可以通过摄像头**实时拍照**，自动裁切为 OOTDiffusion 标准比例
> - 一键进入**触控全屏模式**，专为大屏触摸交互优化的单屏布局
> - 全屏模式下手指滑动浏览衣服、点击放大预览、空槽脉冲引导、延时拍照
> - 4K 屏幕自适应放大，所见即所得
>
> **零后端改动**：所有改动集中在前端，`/api/tryon` 接口及 OOTDiffusion 推理服务完全复用。

---

## 目录

- [一、本次迭代总览](#一本次迭代总览)
- [二、新增功能 1：摄像头实时拍照](#二新增功能-1摄像头实时拍照)
- [三、新增功能 2：OOTDiffusion 标准比例自动裁切](#三新增功能-2ootdiffusion-标准比例自动裁切)
- [四、新增功能 3：触控全屏模式（核心）](#四新增功能-3触控全屏模式核心)
- [五、新增功能 4：4K 大屏自适应](#五新增功能-44k-大屏自适应)
- [六、新增功能 5：触控交互专项优化](#六新增功能-5触控交互专项优化)
- [七、新增功能 6：延时拍照](#七新增功能-6延时拍照)
- [八、文件级改动清单](#八文件级改动清单)
- [九、如何启动（含触控屏部署）](#九如何启动含触控屏部署)
- [十、常见问题与排查](#十常见问题与排查)
- [十一、后续可选优化](#十一后续可选优化)

---

## 一、本次迭代总览

| 模块 | 改动类型 | 说明 |
|---|---|---|
| 摄像头拍照 | **全新功能** | 调用本机/USB 摄像头实时取景拍照，多摄像头切换，权限/异常完整兜底 |
| 自动裁切 | **新增能力** | 拍照画面按中心 3:4 裁切并 resize 至 768×1024，匹配 OOTDiffusion 输入 |
| 触控全屏模式 | **全新模块** | 新增 `/kiosk` 路由 + `KioskView.vue` 单屏布局 + 浏览器原生全屏 API |
| 4K 自适应 | **新增能力** | tailwind 新增 `3xl` 断点，关键元素针对 3840×2160 加大一档 |
| 触控交互优化 | **专项重构** | 去除全屏模式下的文件上传、卡片点击放大、手指滑动 Dock、首次滑动提示、空槽脉冲反馈 |
| 延时拍照 | **新增能力** | 即拍 / 3s / 5s / 10s 倒计时拍照，巨型数字弹出动画 |
| 通用预览弹窗 | **重构** | `ResultModal` 从"试穿结果专用"升级为通用预览，支持人像 / 服装 / 结果三个场景 |
| 后端 | **零改动** | `/api/tryon` 接口、推理逻辑、远程服务全部保持原样 |

---

## 二、新增功能 1：摄像头实时拍照

### 背景

老师希望项目能让用户**用自己作为模特**实时试衣。Mac 上接了 USB 摄像头，需要在
浏览器里调用并拍照、自动上传、和服装搭配生成结果。

### 实现方式

完全使用浏览器原生 [Media Capture API](https://developer.mozilla.org/en-US/docs/Web/API/Media_Capture_and_Streams_API)：
- `navigator.mediaDevices.getUserMedia()` 获取视频流
- `navigator.mediaDevices.enumerateDevices()` 列出所有摄像头（自带 + 外接 USB）
- 用 `<canvas>.drawImage()` 抓帧 + `toBlob()` 生成 `File`
- 通过 `@capture` 事件抛给父组件，复用现有 `onPersonUpload(file)` 上传链路

### 新增组件：`CameraCapture.vue`

弹窗形态，约 540 行，包含：

| 功能 | 实现细节 |
|---|---|
| 多摄像头切换 | 右上下拉框列出所有 `videoinput` 设备（FaceTime + USB），切换瞬间停旧流 → 启新流 |
| 镜像预览开关 | 预览画面 `scale-x-[-1]`（"照镜子"直觉），但**最终图不镜像**避免破坏 OOTDiffusion 姿态识别 |
| 取景辅助层 | 三分线 + 半透明人形剪影 SVG + "对准框内"提示 |
| 加载/错误/重试 | 三态切换；按 `e.name` 给出针对性错误（权限拒绝、设备占用、未连接、API 不支持） |
| 资源管理 | 关闭弹窗、组件卸载、watch `open` 切换时调用 `getTracks().stop()`，避免摄像头一直亮着 |
| 键盘支持 | `Space`/`Enter` 拍照，`Esc` 关闭 |

### 调用入口

在 `ImageSlot.vue` 增加 `capturable` prop，开启后空状态显示
"使用摄像头拍照"按钮，hover 操作层显示"重拍"按钮。

```vue
<ImageSlot
  step="1"
  label="人物图片"
  :preview="personPreview"
  uploadable
  capturable
  @upload="onPersonUpload"
  @capture="cameraOpen = true"
/>
```

### 权限要求

- 必须 `https://` 或 `localhost:` 访问（Web 安全限制）
- macOS 系统设置 → 隐私 → 摄像头 → 允许浏览器
- 首次访问页面会弹一次浏览器权限确认

---

## 三、新增功能 2：OOTDiffusion 标准比例自动裁切

### 背景

OOTDiffusion 的输入尺寸是 **768×1024 (3:4 竖向)**：

```python
# api_server.py:192 (远程推理服务)
model_img = Image.open(io.BytesIO(person_bytes)).convert("RGB").resize((768, 1024))
```

如果直接把摄像头帧（通常 1280×960 或 1280×720）传给后端，被无脑
`resize((768, 1024))` 后人会**横向压扁形变**。

### 解决方案

在前端拍照时就裁好。**所见即所得**：

1. 取景容器锁定 `aspect-[3/4]`，`<video>` 用 `object-cover`
   ——预览画面就是最终上传画面
2. 拍照算法按中心 3:4 cover-crop，输出 768×1024 JPEG

### 核心代码

```javascript
// CameraCapture.vue
const OUTPUT_W = 768
const OUTPUT_H = 1024
const TARGET_RATIO = OUTPUT_W / OUTPUT_H   // = 0.75

function capture() {
  const vw = video.videoWidth, vh = video.videoHeight
  let sx, sy, sw, sh

  if (vw / vh > TARGET_RATIO) {
    // 视频更宽 → 垂直填满，裁左右
    sh = vh
    sw = vh * TARGET_RATIO
    sx = (vw - sw) / 2; sy = 0
  } else {
    // 视频更窄 → 水平填满，裁上下
    sw = vw
    sh = vw / TARGET_RATIO
    sx = 0; sy = (vh - sh) / 2
  }

  canvas.width = OUTPUT_W; canvas.height = OUTPUT_H
  ctx.drawImage(video, sx, sy, sw, sh, 0, 0, OUTPUT_W, OUTPUT_H)
  canvas.toBlob(blob => { capturedBlob = blob }, 'image/jpeg', 0.92)
}
```

### 取景优化

请求摄像头时优先要更高分辨率：

```javascript
const videoConstraints = {
  width:  { ideal: 1920 },
  height: { ideal: 1440 },
  aspectRatio: { ideal: 4 / 3 },
}
```

这样裁切后仍能保留 ≥768×1024 的清晰度。

### 视觉徽章

弹窗顶部显示 `3:4 · 768×1024` 徽章，向用户明示输出规格。

---

## 四、新增功能 3：触控全屏模式（核心）

### 背景

老师希望项目能展示在 **65 寸 16:9 触控屏**（实测分辨率 3840×2160）上，
要求：
1. 全屏沉浸式展示
2. 一屏看完所有功能，不需要滚动
3. 符合触控屏交互习惯

### 实现路径

- 保留 HomeView 原页面**零改动**
- 新增独立 `/kiosk` 路由 + `KioskView.vue`
- 浏览器原生 `requestFullscreen()` API
- 首页 Header 新增"触控全屏"入口

### 16:9 单屏布局

```
┌─────────────────────────────────────────────────────────────────┐
│ Logo · 虚拟试衣 · 触控模式      [触控徽章·分辨率] [重置] [退出全屏] │ ~8%
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    人物图片(3:4)      服装款式(3:4)      试穿结果(3:4)             │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐              │ ~60%
│   │  拍照   │      │ 从Dock选 │      │ 结果展示 │              │
│   └──────────┘      └──────────┘      └──────────┘              │
│                                                                 │
├─ ╌╌╌ 极淡分隔线 ╌╌╌ ────────────────────────────────────────────┤
│  [上半身][下半身][连衣裙]   [⚡ 开始试衣 大按钮]   状态/进度/错误  │ ~11%
├─ ╌╌╌ 极淡分隔线 ╌╌╌ ────────────────────────────────────────────┤
│  服装款式精选 · N 款       [全部][上][下][连衣裙]               │
│ ◀ [👕][👕][👕][👕][👕][👕][👕][👕][👕][👕][👕] ▶              │ ~21%
└─────────────────────────────────────────────────────────────────┘
```

### 关键技术点

#### 1. 自适应槽位宽度

不写死任何分辨率，纯 CSS 计算：

```css
.kiosk-slot-wrap {
  width: clamp(220px, calc((100vh - 620px) * 0.75), 460px);
}
```

- **1080 屏**：槽宽 ~345px / 高 460px
- **1440 屏**：上限 460px
- **4K 屏**：单独媒体查询切换至 ~840px

预算 620px 的 chrome（header + action + dock + 上下呼吸空间），剩余空间
作为槽位高度，再 × 3/4 得槽宽。

#### 2. 全屏 API + 路由联动

```javascript
async function enterKiosk() {
  // 必须由用户手势触发，不能在路由 mounted 里
  if (!document.fullscreenElement) {
    await document.documentElement.requestFullscreen({ navigationUI: 'hide' })
  }
  router.push('/kiosk')
}
```

#### 3. ESC 自动返回

监听 `fullscreenchange`：用户按 ESC 退出全屏 → 自动 `router.push('/')`，
避免被卡在小窗口的 Kiosk 视图里。

```javascript
function onFullscreenChange() {
  if (!document.fullscreenElement) router.push('/')
}
```

#### 4. 三区视觉分隔

操作区上下各一条**极淡渐变分隔线**（白色 8% 透明度），
清晰把"槽位 / 操作 / Dock"三个功能区分开：

```css
.kiosk-action::before,
.kiosk-action::after {
  content: '';
  position: absolute;
  height: 1px;
  background: linear-gradient(
    90deg, transparent 0%,
    rgba(255,255,255,0.08) 30%,
    rgba(255,255,255,0.08) 70%,
    transparent 100%
  );
}
```

---

## 五、新增功能 4：4K 大屏自适应

### 背景

3840×2160 是 1080 的精确 2 倍。Tailwind 默认断点最大 `2xl=1536`，
4K 屏会触发但元素尺寸是基于 1080 设计的，**所有按钮/字号/卡片显得过小**。

### 解决方案

#### 1. 新增 `3xl: '2400px'` 断点

```javascript
// tailwind.config.js
theme: {
  extend: {
    screens: {
      // 4K 大屏断点（65 寸触控屏 3840×2160 会命中）
      '3xl': '2400px',
    },
  },
}
```

> 为什么是 2400 而不是 3000？因为 2560×1440 显示器很常见，
> 想让它也享受 4K 加大版的尺寸（不至于元素偏小）。
> 如果只想真正 4K 才生效，把数值改成 '3200px' 即可。

#### 2. 关键元素加 3xl 变体

| 元素 | 1080 屏 | 4K 屏 |
|---|---|---|
| Logo 方块 | 56×56 | 96×96 |
| 主标题字号 | text-2xl (24px) | text-5xl (48px) |
| 槽位宽度 | ~420px | **840px** |
| "开始试衣"按钮 | px-14 py-5 text-lg | **px-24 py-8 text-3xl** |
| 分类切换按钮 | px-5 py-2.5 text-sm | px-8 py-4 text-xl |
| Dock 衣服卡片 | 152×203 | **240×320** |
| Dock 左右导航圆按钮 | 56×56 | **96×96** |
| 单次滚动距离 | 480px | 880px |
| 操作行内边距 py | 7 (28px) | 12 (48px) |

#### 3. 4K 布局数学验证

```
3840 宽度上：
  3 槽 × 840px + 2 × gap-20(80px) + 左右 px-24(96px×2) = 2712px
  → 居中显示，两侧 ~564px 留白 ✓

2160 高度上：
  Header ~180 + Action ~160 + Dock ~480 = 820px (chrome)
  主区可用：1340px
  槽位实际高度：840 × 4/3 + 标签 50 = 1170px
  → 上下 ~85px 余量 ✓
```

---

## 六、新增功能 5：触控交互专项优化

### 设计原则

触控屏没有鼠标 hover，没有键盘，操作方式只剩**手指点 + 手指滑**。
原有的 Mac 风 Dock 鼠标距离放大、hover 出按钮等设计在触控屏上无效。

### 1. 全屏模式去除文件上传

人物只能拍照，衣服只能从 Dock 选取：

```vue
<!-- 人物：只允许拍照，不允许上传 -->
<ImageSlot
  step="1"
  capturable
  :zoomable="!!personPreview"
  @capture="cameraOpen = true"
  @zoom="openZoom(personPreview, '人像预览', false)"
/>

<!-- 衣服：只允许从 Dock 选取，不允许上传 -->
<ImageSlot
  step="2"
  :zoomable="!!clothPreview"
  @zoom="openZoom(clothPreview, '服装预览', false)"
  @empty-click="pulseDock"
/>
```

### 2. 整张卡片可点击（巨型触控目标）

修改了 `ImageSlot.onCardClick` 逻辑：

```javascript
function onCardClick() {
  if (props.loading) return
  if (props.preview && props.zoomable)             emit('zoom')      // 有图 → 放大
  else if (!props.preview && props.capturable && !props.uploadable)
                                                    emit('capture')   // 空 + 仅拍照 → 开摄像头
  else if (props.uploadable)                       triggerInput()    // 默认上传
  else                                              emit('emptyClick')// 兜底
}
```

| 槽位 | 空状态点击 | 有内容点击 |
|---|---|---|
| 人物 | 开摄像头 | 放大预览 |
| 衣服 | 脉冲 Dock 引导 | 放大预览 |
| 结果 | 无响应 | 放大预览（带下载按钮） |

### 3. 手指滑动 Dock

底部衣服 Dock 在触控屏上原生支持手指滑动（`overflow-x: auto`），
但加了几个体验增强：

```css
.kiosk-dock-scroller {
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  scroll-snap-type: x proximity;       /* 滑停后自动吸附 */
}

.snap-card {
  scroll-snap-align: start;
  scroll-snap-stop: always;             /* 避免飞过太多卡片 */
}

.kiosk-dock-card {
  touch-action: pan-x;
  -webkit-tap-highlight-color: transparent;
}
```

### 4. 首次滑动提示

用户不知道能滑？显示一个**左右摆动的提示徽章**：

```vue
<div v-if="showSwipeHint" class="swipe-hint-anim">
  <span class="text-accent">←</span> 手指滑动浏览更多
</div>
```

- 显示条件：`canScrollRight && !hasSwiped`
- 用户一旦滑动或点过左右箭头 → `hasSwiped = true` → 提示永久消失
- 动画：左右摆动 14px 循环

### 5. 空衣服槽脉冲反馈

用户点了"还没选衣服"的卡片 → Dock 整体上浮 + 发光 1.4s：

```css
@keyframes dock-pulse {
  0%   { filter: drop-shadow(0 0 0 rgba(200,255,61,0)); transform: translateY(0); }
  20%  { filter: drop-shadow(0 -6px 28px rgba(200,255,61,0.45)); transform: translateY(-4px); }
  60%  { filter: drop-shadow(0 -3px 16px rgba(200,255,61,0.25)); transform: translateY(0); }
  100% { filter: drop-shadow(0 0 0 rgba(200,255,61,0)); transform: translateY(0); }
}
```

视觉上明确告诉用户"去看下面"。

### 6. 通用预览弹窗

`ResultModal` 升级，新增 `title` / `showDownload` / `downloadName` 三个 props：

```vue
<ResultModal
  :open="zoomOpen"
  :src="zoomSrc"
  :title="zoomTitle"            <!-- "人像预览" / "服装预览" / "试穿结果预览" -->
  :show-download="zoomDownload" <!-- 只有结果允许下载 -->
/>
```

KioskView 用一个 modal 实例服务 3 个槽位，状态化管理。

### 7. 顶部"重置"按钮

公开展示场景关键功能：一键清空所有状态，方便下一位用户使用。

### 8. 实时分辨率徽章

顶部徽章显示当前视口分辨率（如 `3840×2160`），调试/演示用。

---

## 七、新增功能 6：延时拍照

### 背景

用户在 65 寸触控屏前没办法**自己按拍照键**——按完键还要跑回画面里站好。
经典相机的"自拍延时"功能解决这个问题。

### 选项

- **即拍**（0 秒，默认）
- **3 秒**
- **5 秒**
- **10 秒**

### 交互流程

```
[用户选 3 秒] → [点击 "3 秒后拍照"]
        ↓
[画面中央出现巨大数字 3] (脉冲发光)
        ↓ 1s
[2] → [1] → [拍照]
        ↓
[显示预览 + 重拍 / 使用这张]
```

### 视觉效果

倒计时数字用 `clamp(120px, 28vh, 280px)` 自适应大小，
配合 `text-shadow` 制造 accent 色发光晕，每秒切换时弹出动画：

```css
@keyframes count-pop {
  0%   { transform: scale(0.4); opacity: 0; }
  30%  { transform: scale(1.15); opacity: 1; }
  60%  { transform: scale(1.00); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.85; }
}
```

`:key="countdown"` 绑定让每个新数字触发新 DOM 节点，
动画自动重播，呈现"3 砰、2 砰、1 砰"的节奏。

### 取消机制

支持多入口取消，鲁棒性强：

| 入口 | 行为 |
|---|---|
| "取消倒计时"按钮 | 取消，回到准备态 |
| ESC 键（倒计时中） | 优先取消倒计时，**不关闭弹窗** |
| 切换摄像头下拉 | 自动取消（避免拍到切换间隙的黑帧） |
| 关闭 X / 点遮罩 | 关闭弹窗 + 清理定时器 |
| 组件卸载 | `onBeforeUnmount` 清理定时器 |

### 默认值兼容

`delaySeconds` 默认为 `0`（即拍），所以**不需要延时的用户体验完全不受影响**，
HomeView 和 Kiosk 共用此组件，行为一致。

---

## 八、文件级改动清单

### 新增文件 (2)

| 文件 | 行数 | 作用 |
|---|---|---|
| `frontend/src/components/CameraCapture.vue` | ~580 | 摄像头拍照弹窗 + 延时拍照 + 3:4 自动裁切 |
| `frontend/src/views/KioskView.vue` | ~580 | 16:9 触控大屏单屏布局，专为 65 寸 4K 屏设计 |

### 修改文件 (5)

| 文件 | 改动内容 |
|---|---|
| `frontend/src/components/ImageSlot.vue` | 新增 `capturable` prop；`onCardClick` 增加 capture-only 分支；新增 `IconCamera` 组件；新增 `emptyClick` 事件 |
| `frontend/src/components/ResultModal.vue` | 新增 `title` / `showDownload` / `downloadName` props，升级为通用预览弹窗；顶部工具栏加 `3xl:` 适配 4K |
| `frontend/src/views/HomeView.vue` | Header 增加"触控全屏"入口按钮 + `enterKiosk` 方法；人物槽位增加 `capturable` |
| `frontend/src/router/index.js` | 增加 `/kiosk` 路由 |
| `frontend/tailwind.config.js` | `theme.extend.screens` 新增 `3xl: '2400px'` 断点 |

### 后端文件

**全部零改动**。`/api/tryon` 接口、远程 OOTDiffusion 推理服务、HD/DC 路由
全部沿用上次迭代的逻辑。

---

## 九、如何启动

### 1. 桌面开发模式（与之前一致）

```bash
# 终端 1：后端(mac)
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# 终端 2：前端
cd frontend
npm install   # 首次需要
npm run dev
```

访问 `http://localhost:5173`。

### 2. 远程推理服务（OOTDiffusion）

如果用远程 GPU 服务器跑推理，仍需先把端口映射过来：

```bash
ssh -L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001 user@server
```

服务器上：

```bash
# HD 模型（上半身）
python api_server.py --gpu_id 0 --port 9000 --model_type hd --n_samples 4 --scale 2.0

# DC 模型（下半身 / 连衣裙）
python api_server.py --gpu_id 0 --port 9001 --model_type dc --n_samples 4 --scale 2.0
```

### 3. 摄像头权限准备

第一次拍照前需要授权：

#### 浏览器权限
- 首次点拍照时浏览器会弹"允许使用摄像头吗？"，点允许
- 如果误点拒绝：地址栏左侧🔒图标 → 摄像头 → 允许 → 刷新页面

#### macOS 系统权限
- 系统设置 → 隐私与安全性 → 摄像头 → 勾选你用的浏览器（Chrome/Safari/Edge）
- 改完需要重启浏览器才生效

#### USB 摄像头连接
- 确认 USB 摄像头已物理连接
- 在"系统报告 → USB"里能看到设备
- 浏览器弹窗内右上角下拉框应能看到"USB Camera"或类似名称

### 4. 65 寸 4K 触控屏部署

#### 准备
1. 把项目部署到一台能访问触控屏的电脑（Mac mini / Windows mini PC 等）
2. 把电脑接到触控屏的 HDMI/USB-C 输入
3. **触控反向连接**：触控屏 USB 接到电脑，确认电脑能识别为触摸输入设备

#### 启动 Chrome 进入展示模式

```bash
# macOS
open -a "Google Chrome" --args \
  --kiosk \
  --start-fullscreen \
  --disable-pinch \
  --overscroll-history-navigation=0 \
  http://localhost:5173/kiosk

# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --kiosk ^
  --start-fullscreen ^
  --disable-pinch ^
  http://localhost:5173/kiosk
```

参数说明：
- `--kiosk`：无地址栏、无菜单的展示模式
- `--start-fullscreen`：启动即全屏
- `--disable-pinch`：禁用触控屏双指缩放（避免误操作）
- `--overscroll-history-navigation=0`：禁用左滑后退（避免触摸滑动误退出）

#### 如果不用 Chrome kiosk 参数

直接访问 `http://localhost:5173/` → 点击右上角"触控全屏"按钮，
浏览器会请求全屏权限，授权后进入 Kiosk 视图。

### 5. 验证清单

部署完后逐项验证：

- [ ] 桌面访问 `/` 正常显示（HomeView 原样）
- [ ] 点击"触控全屏" → 浏览器全屏 → 跳转到 `/kiosk`
- [ ] Kiosk 界面三栏布局正确，无滚动条
- [ ] 4K 屏上字号/按钮/卡片明显放大
- [ ] 人物槽点击 → 弹出摄像头弹窗
- [ ] 摄像头能列出 USB 设备并切换
- [ ] 选 3/5/10 秒延时 → 倒计时数字弹出
- [ ] 拍照后图片是 768×1024（在 Chrome DevTools 看请求的 multipart 内容）
- [ ] 衣服 Dock 手指滑动顺滑，首次显示"← 手指滑动浏览更多"提示
- [ ] 人物/衣服/结果三张图都能点击放大
- [ ] 试衣完整流程跑通，生成结果可下载
- [ ] 点"重置" → 所有状态清空
- [ ] 按 ESC → 自动退出全屏并返回首页

---

## 十、常见问题与排查

### Q1: 摄像头打不开，提示"权限被拒绝"

按这个顺序检查：

1. **是不是 HTTPS 或 localhost**：`getUserMedia` 在 `http://` 非 localhost 上不可用
2. **浏览器权限**：地址栏左侧🔒图标 → 重置权限 → 刷新
3. **系统权限**：macOS 系统设置 → 隐私 → 摄像头 → 允许浏览器
4. **设备占用**：关闭 FaceTime / Zoom / 飞书 / 钉钉等可能占用摄像头的应用

错误弹窗会根据 `e.name` 自动给出针对性提示。

### Q2: 拍出来的人像还是被压扁了

应该不会出现。如果出现说明前端裁切失败：
- 在浏览器 DevTools → Network 看 `/api/tryon` 请求里 `person` 字段的图片，
  右键保存查看尺寸应该精确为 **768×1024**
- 如果不是，看 Console 是否有 canvas 报错

### Q3: 4K 屏上元素还是显得小

确认 `tailwind.config.js` 修改后**重新启动了 dev server**：

```bash
cd frontend
# Ctrl+C 停止现有 npm run dev
npm run dev
```

Tailwind 配置改动需要重新构建。

### Q4: 触控屏上手指滑动 Dock 没反应

检查：
1. 是否真的进入了 `/kiosk` 模式（HomeView 的旧 Dock 没做触控优化）
2. 浏览器是否禁用了触控事件（Chrome 启动加 `--disable-pinch` 不要禁用 touch）
3. 触摸屏驱动是否正常（系统设置里能识别多点触控输入）

### Q5: 全屏模式按 ESC 后回到了首页，但浏览器没退出全屏

某些浏览器有自己的全屏控制。先按 `Esc` 退出全屏，再点首页"触控全屏"重进。

### Q6: 倒计时进行中切换了摄像头，结果黑屏

已修复：`restartStream` 会自动 `cancelCountdown()`，
防止拍到摄像头切换间隙的黑帧。

### Q7: 65 寸屏上想再大一点 / 再小一点

调整两个值：

```javascript
// tailwind.config.js
'3xl': '2400px',  // ← 改这个数值控制何时触发 4K 加大版
                  //   想 2K 屏也用大尺寸：值改小（如 2000）
                  //   想只 4K 才用大尺寸：值改大（如 3200）
```

```css
/* KioskView.vue */
@media (min-width: 2400px) {
  .kiosk-slot-wrap {
    width: clamp(420px, calc((100vh - 980px) * 0.75), 840px);
    /*                                              ^^^ 槽位最大宽度 */
  }
}
```

---

## 十一、后续可选优化

下次迭代可以考虑：

### A. 流程闭环
- **拍照确认后自动脉冲 Dock**：引导用户去选衣服，无缝衔接下一步
- **试衣完成后自动放大结果**：省一次点击

### B. 展示场景必备
- **空闲超时自动重置**：30 秒无操作自动 `resetAll()`，下个顾客一来就是干净状态
- **结果二维码**：扫码下载到手机（实地展示时用户带不走 65 寸屏）

### C. 拍照增强
- **倒计时滴答音效**：3-2-1 配 beep 声，最后一秒 ding，更有相机感
- **自拍美颜滤镜**：通过 WebGL 简单磨皮 / 调色

### D. 衣服 Dock
- **当前选中自动滚动到视口中央**：用户切换分类时清晰看到选中状态
- **多选试穿队列**：连续选 3 件衣服自动跑 3 次试衣

### E. 后端补强
- **后端兜底 cover-crop**：万一前端拍照失败，后端 PIL 再做一次中心裁切
- **结果图历史**：保存生成记录，触控屏右侧或角落显示"刚才大家试过的"

### F. 数据观察
- **使用统计**：拍照次数、试衣次数、热门服装排行，给老师做展示报告

---

## 附：核心文件目录

```
virtual-tryon/
├── backend/                                  # 后端（本次零改动）
│   ├── main.py                               # FastAPI 主入口
│   ├── admin.py                              # 后台管理路由
│   ├── storage.py                            # 衣服 JSON 持久化
│   └── ...
├── frontend/
│   ├── tailwind.config.js                    # 🔧 加 3xl 断点
│   └── src/
│       ├── router/
│       │   └── index.js                      # 🔧 加 /kiosk 路由
│       ├── views/
│       │   ├── HomeView.vue                  # 🔧 加触控全屏入口
│       │   ├── KioskView.vue                 # ✨ 全新：16:9 触控全屏视图
│       │   ├── AdminView.vue
│       │   └── AdminLoginView.vue
│       └── components/
│           ├── ImageSlot.vue                 # 🔧 加 capturable + capture-only 点击
│           ├── ResultModal.vue               # 🔧 升级为通用预览弹窗
│           ├── CameraCapture.vue             # ✨ 全新：摄像头拍照 + 延时 + 自动裁切
│           ├── ClothingDock.vue              # （未改）原 Dock，HomeView 用
│           ├── ProgressBar.vue
│           └── AdminClothesGrid.vue / AdminUploader.vue
├── OOTDiffusion/                             # 推理代码（远程）
│   └── run/api_server.py                     # 768×1024 标准输入
├── CHANGELOG_2026-04-23.md                   # 上次迭代
└── CHANGELOG_2026-05-15.md                   # 👈 本次（你正在看的这份）
```

图例：✨ = 新增；🔧 = 修改

---

**迭代完成时间**：2026-05-15 22:30

**核心成果**：从"桌面端 Web 应用"升级为"桌面 + 65 寸 4K 触控屏双形态应用"，
新增 6 项功能（摄像头拍照、3:4 自动裁切、触控全屏模式、4K 自适应、触控交互优化、延时拍照），
零后端改动，向后完全兼容。
