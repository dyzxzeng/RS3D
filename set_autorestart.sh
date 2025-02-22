#!/bin/bash

# Find the read_data.py file
SCRIPT_PATH=$(find /home -name "read_data.py" 2>/dev/null | head -n 1)

if [ -z "$SCRIPT_PATH" ]; then
    echo "Error: read_data.py not found!"
    exit 1
fi

PYTHON_PATH=$(which python3)
SERVICE_FILE="/etc/systemd/system/read_data.service"
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")  # Get the directory where read_data.py is located

# Print information
echo "Found read_data.py at: $SCRIPT_PATH"
echo "Using Python at: $PYTHON_PATH"
echo "Service file will be created at: $SERVICE_FILE"
echo "Logs will be stored in: $SCRIPT_DIR"

# Create the systemd service file
echo "Creating systemd service file..."
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

# Set correct permissions
sudo chmod 644 $SERVICE_FILE

# Reload systemd configuration
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Start and enable the service
echo "Starting and enabling the service..."
sudo systemctl start read_data.service
sudo systemctl enable read_data.service

echo "Done! read_data.service is now set up and running."
