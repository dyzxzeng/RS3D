#!/bin/bash

# 查找 read_data.py 文件
SCRIPT_PATH=$(find /home -name "read_data.py" 2>/dev/null | head -n 1)

if [ -z "$SCRIPT_PATH" ]; then
    echo "❌ Error: read_data.py not found!"
    exit 1
fi

PYTHON_PATH=$(which python3)
SERVICE_FILE="/etc/systemd/system/read_data.service"
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")  # 获取 read_data.py 所在目录

# 打印信息
echo "✅ Found read_data.py at: $SCRIPT_PATH"
echo "🐍 Using Python at: $PYTHON_PATH"
echo "📝 Service file will be created at: $SERVICE_FILE"
echo "📂 Logs will be stored in: $SCRIPT_DIR"

# 创建 systemd service 文件
echo "🚀 Creating systemd service file..."
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Run read_data.py on startup
After=network.target

[Service]
ExecStart=$PYTHON_PATH $SCRIPT_PATH
WorkingDirectory=$SCRIPT_DIR
StandardOutput=append:$SCRIPT_DIR/read_data.log
StandardError=append:$SCRIPT_DIR/read_data_error.log
Restart=always
RestartSec=30
TimeoutStartSec=300
User=pi

[Install]
WantedBy=multi-user.target
EOF

# 赋予正确的权限
sudo chmod 644 $SERVICE_FILE

# 重新加载 systemd 配置
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# 启动并启用服务
echo "🚀 Starting and enabling the service..."
sudo systemctl start read_data.service
sudo systemctl enable read_data.service

echo "✅ Done! read_data.service is now set up and running."
