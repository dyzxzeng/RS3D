#!/bin/bash

SERVICE_FILE="/etc/systemd/system/read_data.service"
PYTHON_PATH=$(which python3)
SCRIPT_PATH="/home/pi/read_data.py"

# 创建 systemd service 文件
echo "Creating systemd service file..."
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Run read_data.py on startup
After=network.target

[Service]
ExecStart=$PYTHON_PATH $SCRIPT_PATH
WorkingDirectory=/home/pi
StandardOutput=append:/home/pi/read_data.log
StandardError=append:/home/pi/read_data_error.log
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
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# 启动并启用服务
echo "Starting and enabling the service..."
sudo systemctl start read_data.service
sudo systemctl enable read_data.service

echo "Done! read_data.service is now set up."
