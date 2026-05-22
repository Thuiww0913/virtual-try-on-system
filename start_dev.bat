@echo off
chcp 65001 > nul
REM ===========================================================
REM Virtual Try-On 一键启动脚本(Windows 服务器)
REM ===========================================================
REM 会同时打开 3 个 cmd 窗口:
REM   1) Backend  —— 进入 backend 目录,激活 conda dev 环境,uvicorn 启动
REM   2) Frontend —— 进入 frontend 目录,npm run dev 启动 Vite
REM   3) SSH Tunnel —— 把 GPU 服务器的 9000 / 9001 端口映射过来
REM
REM 关闭只需各窗口里 Ctrl+C 或直接 X 关窗。
REM ===========================================================

setlocal
set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%virtual-tryon\backend"
set "FRONTEND_DIR=%ROOT%virtual-tryon\frontend"

echo.
echo  Virtual Try-On 启动中...
echo  项目根目录: %ROOT%
echo.

REM ── 1. 后端 ─────────────────────────────────────────────
echo  [1/3] 启动后端 (uvicorn @ 8000)...
start "Backend - uvicorn" cmd /k "cd /d ""%BACKEND_DIR%"" && call conda activate dev && uvicorn main:app --reload --port 8000"

REM 间隔一下,避免 3 个窗口挤在一起触发(可选)
timeout /t 1 /nobreak > nul

REM ── 2. 前端 ─────────────────────────────────────────────
echo  [2/3] 启动前端 (Vite dev server)...
start "Frontend - vite" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev"

timeout /t 1 /nobreak > nul

REM ── 3. SSH 隧道 ──────────────────────────────────────────
echo  [3/3] 建立 SSH 隧道 (GPU 服务器 9000/9001)...
echo       提示:首次连接可能需要输入密码或确认指纹
start "SSH Tunnel - GPU Server" cmd /k "ssh -p 3485 -L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001 root@172.24.246.49"

echo.
echo  全部启动完成!请在弹出的三个 cmd 窗口里观察:
echo    - Backend  :http://127.0.0.1:8000
echo    - Frontend :http://localhost:5173
echo    - SSH      :HD=9000  DC=9001
echo.
echo  按任意键关闭本窗口(三个子窗口会继续运行)
pause > nul
endlocal
