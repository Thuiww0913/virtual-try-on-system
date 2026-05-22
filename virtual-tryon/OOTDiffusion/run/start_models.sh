#!/usr/bin/env bash
# ===========================================================
# OOTDiffusion 双模型一键启动(Linux GPU 服务器)
# ===========================================================
# 在当前目录后台启动两个 api_server.py:
#   - HD 模型 (upperbody 专用,质量最佳) :9000
#   - DC 模型 (lowerbody / dress)        :9001
#
# 日志:  logs/hd.log  / logs/dc.log
# PID:   logs/hd.pid  / logs/dc.pid (供 stop_models.sh 使用)
#
# 关闭 SSH 会话后两个进程仍会继续运行(nohup)。
# 停止用 ./stop_models.sh
# ===========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 激活 conda 环境 ────────────────────────────────────────
# 兼容 anaconda / miniconda 两种常见安装路径
CONDA_SH=""
for candidate in \
    "$HOME/anaconda3/etc/profile.d/conda.sh" \
    "$HOME/miniconda3/etc/profile.d/conda.sh" \
    "/opt/anaconda3/etc/profile.d/conda.sh" \
    "/opt/miniconda3/etc/profile.d/conda.sh" \
    "/root/anaconda3/etc/profile.d/conda.sh" \
    "/root/miniconda3/etc/profile.d/conda.sh"
do
    if [ -f "$candidate" ]; then
        CONDA_SH="$candidate"
        break
    fi
done

if [ -z "$CONDA_SH" ]; then
    echo "[ERROR] 找不到 conda.sh,请手动修改本脚本里的 CONDA_SH 路径"
    echo "        提示:运行 'conda info --base' 查看 conda 安装位置"
    exit 1
fi

# shellcheck disable=SC1090
source "$CONDA_SH"
conda activate ootdiffusion

# ── 准备日志目录 ───────────────────────────────────────────
mkdir -p logs

# ── 检查是否已在运行 ───────────────────────────────────────
check_running() {
    local pid_file="logs/$1.pid"
    if [ -f "$pid_file" ]; then
        local old_pid
        old_pid=$(cat "$pid_file")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "[WARN] $1 模型似乎已在运行 (pid=$old_pid),先停止再重新启动:"
            echo "       ./stop_models.sh"
            exit 1
        fi
    fi
}
check_running hd
check_running dc

# ── 启动 HD 模型 (port 9000) ───────────────────────────────
echo "[1/2] 启动 HD 模型 (upperbody) on port 9000..."
nohup python api_server.py \
    --gpu_id 0 \
    --port 9000 \
    --model_type hd \
    --n_samples 4 \
    --scale 2.0 \
    > logs/hd.log 2>&1 &
HD_PID=$!
echo $HD_PID > logs/hd.pid
echo "      pid=$HD_PID  log=logs/hd.log"

# 小等一下,让 HD 先抢占 GPU 缓存空间
sleep 3

# ── 启动 DC 模型 (port 9001) ───────────────────────────────
echo "[2/2] 启动 DC 模型 (lowerbody/dress) on port 9001..."
nohup python api_server.py \
    --gpu_id 0 \
    --port 9001 \
    --model_type dc \
    --n_samples 4 \
    --scale 2.0 \
    > logs/dc.log 2>&1 &
DC_PID=$!
echo $DC_PID > logs/dc.pid
echo "      pid=$DC_PID  log=logs/dc.log"

echo ""
echo "✓ 两个模型已在后台启动,日志在 $SCRIPT_DIR/logs/"
echo ""
echo "实时查看日志:"
echo "  tail -f logs/hd.log    # HD 模型"
echo "  tail -f logs/dc.log    # DC 模型"
echo ""
echo "停止两个模型:"
echo "  ./stop_models.sh"
echo ""
echo "模型加载需要 30s ~ 2min,等到日志里出现 'Uvicorn running on ...' 才算完全就绪。"
