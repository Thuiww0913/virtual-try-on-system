#!/usr/bin/env bash
# ===========================================================
# OOTDiffusion 双模型一键停止(Linux GPU 服务器)
# ===========================================================
# 读取 logs/hd.pid 和 logs/dc.pid,逐一 kill。
# 如果 PID 文件缺失,会尝试从端口反查进程。
# ===========================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

stop_one() {
    local name=$1     # hd / dc
    local port=$2     # 9000 / 9001
    local pid_file="logs/$name.pid"
    local pid=""

    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
    fi

    # PID 文件不存在或进程已挂,从端口反查一次
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        if command -v lsof &>/dev/null; then
            pid=$(lsof -ti tcp:"$port" 2>/dev/null || true)
        elif command -v fuser &>/dev/null; then
            pid=$(fuser -n tcp "$port" 2>/dev/null | tr -d ' ' || true)
        fi
    fi

    if [ -z "$pid" ]; then
        echo "[$name] 未运行(端口 $port 上无进程)"
        rm -f "$pid_file"
        return
    fi

    echo "[$name] 停止 pid=$pid (port=$port)..."
    kill "$pid" 2>/dev/null || true

    # 等待 5 秒优雅退出,否则强杀
    for i in 1 2 3 4 5; do
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
        echo "      未在 5s 内退出,使用 kill -9 强制终止"
        kill -9 "$pid" 2>/dev/null || true
    fi

    rm -f "$pid_file"
    echo "      已停止"
}

stop_one hd 9000
stop_one dc 9001

echo ""
echo "✓ 双模型已停止"
