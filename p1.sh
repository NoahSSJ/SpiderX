#!/bin/bash
pname="python a.py"     # 用完整命令匹配
sname="fbs"
workdir="/root/some"

# 1. 判断目标进程是否在跑
if ! pgrep -f "$pname" > /dev/null; then
    echo "$pname 不存在，准备拉起"

    # 2. 确保 tmux 会话存在（-d 后台创建，不 attach）
    if ! tmux has-session -t "$sname" 2>/dev/null; then
        tmux new-session -d -s "$sname" -c "$workdir"
    fi

    # 3. 往会话里发命令启动程序
    tmux send-keys -t "$sname" "cd $workdir && python bilibili.py" Enter

    sleep 2
    if pgrep -f "$pname" > /dev/null; then
        echo "启动成功"
    else
        echo "启动失败，请人工介入"
    fi
else
    echo "$pname 正常运行"
fi