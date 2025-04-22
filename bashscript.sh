#!/bin/bash

# Update system and install dependencies
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv mitmproxy chromium-browser chromium-chromedriver xvfb

# Create project directory structure (if not exists)
PROJECT_DIR="/home/ubuntu/FinancialJuiceScrapper"
mkdir -p $PROJECT_DIR

# Create virtual environment
VENV_DIR="/home/ubuntu/financialjuice_venv"
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install flask selenium mitmproxy pyvirtualdisplay

# Create systemd service files

## 1. Flask App Service
sudo tee /etc/systemd/system/financialjuice-app.service > /dev/null <<EOL
[Unit]
Description=FinancialJuice Flask Application
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

## 2. MITM Proxy Service
sudo tee /etc/systemd/system/financialjuice-mitmproxy.service > /dev/null <<EOL
[Unit]
Description=FinancialJuice MITM Proxy
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$VENV_DIR/bin/mitmdump -s $PROJECT_DIR/ws_interceptor.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

## 3. Selenium Scraper Service (with virtual display)
sudo tee /etc/systemd/system/financialjuice-scraper.service > /dev/null <<EOL
[Unit]
Description=FinancialJuice Selenium Scraper
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="DISPLAY=:99"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/scrapper.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd to recognize new services
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable financialjuice-app.service
sudo systemctl enable financialjuice-mitmproxy.service
sudo systemctl enable financialjuice-scraper.service

sudo systemctl start financialjuice-app.service
sudo systemctl start financialjuice-mitmproxy.service
sudo systemctl start financialjuice-scraper.service

echo "Setup complete! Services are now running."
echo "To check status:"
echo "  sudo systemctl status financialjuice-app"
echo "  sudo systemctl status financialjuice-mitmproxy"
echo "  sudo systemctl status financialjuice-scraper"