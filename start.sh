#!/bin/bash

# ==================== 配置 ====================
APP_NAME="Flask Application"
PYTHON_CMD="python3"
MAIN_FILE="main.py"
LOG_FILE="app.log"
PORT=9999

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 函数定义 ====================

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 获取进程 PID
get_pid() {
    ps aux | grep "$MAIN_FILE" | grep -v grep | awk '{print $2}'
}

# 检查进程是否运行
is_running() {
    if [ -z "$(get_pid)" ]; then
        return 1
    else
        return 0
    fi
}

# 启动服务
start_service() {
    print_info "启动 $APP_NAME..."
    
    # 检查文件是否存在
    if [ ! -f "$MAIN_FILE" ]; then
        print_error "$MAIN_FILE 文件不存在"
        return 1
    fi
    
    # 检查端口是否被占用
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "端口 $PORT 已被占用"
        print_info "正在杀死占用该端口的进程..."
        lsof -i :$PORT -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    # 启动应用
    nohup $PYTHON_CMD $MAIN_FILE > $LOG_FILE 2>&1 &
    
    sleep 2
    
    if is_running; then
        PID=$(get_pid)
        print_success "服务启动成功！"
        print_info "PID: $PID"
        print_info "日志文件: $LOG_FILE"
        print_info "访问地址: http://localhost:$PORT/hello"
        return 0
    else
        print_error "服务启动失败！"
        print_info "错误信息："
        cat $LOG_FILE
        return 1
    fi
}

# 停止服务
stop_service() {
    print_info "停止 $APP_NAME..."
    
    if ! is_running; then
        print_warning "服务未运行"
        return 0
    fi
    
    PID=$(get_pid)
    print_info "正在停止 PID: $PID..."
    
    kill -15 $PID 2>/dev/null
    sleep 2
    
    # 如果还未停止，强制杀死
    if is_running; then
        print_warning "进程未响应，强制杀死..."
        kill -9 $PID 2>/dev/null
    fi
    
    if ! is_running; then
        print_success "服务停止成功！"
        return 0
    else
        print_error "服务停止失败！"
        return 1
    fi
}

# 重启服务
restart_service() {
    print_info "重启 $APP_NAME..."
    stop_service
    sleep 1
    start_service
}

# 查看服务状态
status_service() {
    if is_running; then
        PID=$(get_pid)
        print_success "服务正在运行 (PID: $PID)"
        
        # 显示进程信息
        echo ""
        ps aux | grep $MAIN_FILE | grep -v grep
        
        # 检查端口
        echo ""
        print_info "端口监听状态:"
        netstat -tulpn 2>/dev/null | grep $PORT || lsof -i :$PORT 2>/dev/null
        
        return 0
    else
        print_warning "服务未运行"
        return 1
    fi
}

# 查看日志
view_log() {
    if [ ! -f "$LOG_FILE" ]; then
        print_error "日志文件不存在: $LOG_FILE"
        return 1
    fi
    
    print_info "显示最后 50 行日志 (按 Ctrl+C 退出)..."
    echo ""
    tail -f $LOG_FILE
}

# 查看日志（最后 N 行）
view_log_lines() {
    local lines=${1:-50}
    
    if [ ! -f "$LOG_FILE" ]; then
        print_error "日志文件不存在: $LOG_FILE"
        return 1
    fi
    
    print_info "显示最后 $lines 行日志"
    echo ""
    tail -n $lines $LOG_FILE
}

# 测试服务
test_service() {
    print_info "测试服务..."
    
    if ! is_running; then
        print_error "服务未运行，请先启动"
        return 1
    fi
    
    sleep 1
    
    print_info "测试 /hello 接口..."
    response=$(curl -s http://localhost:$PORT/hello)
    
    if [ -z "$response" ]; then
        print_error "无响应"
        return 1
    fi
    
    if echo "$response" | grep -q "hello"; then
        print_success "接口响应正常: $response"
        return 0
    else
        print_error "接口响应异常: $response"
        return 1
    fi
}

# 清空日志
clear_log() {
    print_info "清空日志文件..."
    
    if [ -f "$LOG_FILE" ]; then
        > $LOG_FILE
        print_success "日志已清空"
    else
        print_warning "日志文件不存在"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
${BLUE}========================================${NC}
${GREEN}Flask 应用管理脚本${NC}
${BLUE}========================================${NC}

用法: $0 <命令> [选项]

${GREEN}命令:${NC}
  start       启动服务
  stop        停止服务
  restart     重启服务
  status      查看服务状态
  log         查看实时日志
  log <N>     查看最后 N 行日志
  test        测试服务
  clear       清空日志文件
  help        显示此帮助信息

${GREEN}示例:${NC}
  $0 start              # 启动服务
  $0 stop               # 停止服务
  $0 restart            # 重启服务
  $0 status             # 查看状态
  $0 log                # 查看实时日志
  $0 log 100            # 查看最后 100 行日志
  $0 test               # 测试服务

${BLUE}========================================${NC}
EOF
}

# ==================== 主逻辑 ====================

# 检查参数
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# 处理命令
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    log)
        if [ -z "$2" ]; then
            view_log
        else
            view_log_lines $2
        fi
        ;;
    test)
        test_service
        ;;
    clear)
        clear_log
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

exit $?

