#!/bin/bash
# Server setup script for Ubuntu 22.04

set -e

echo "🔧 CodeReview Bot Server Setup"
echo "=============================="

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Install Git
echo "📦 Installing Git..."
apt install -y git

# Create app directory
APP_DIR="/opt/codereview-bot"
echo "📁 Creating application directory: $APP_DIR"
mkdir -p $APP_DIR

# Clone or update repository
if [ -d "$APP_DIR/.git" ]; then
    echo "📥 Updating existing repository..."
    cd $APP_DIR
    git pull
else
    echo "📥 Cloning repository..."
    # Replace with your actual repository URL
    echo "⚠️  Note: Update this script with your actual Git repository URL"
    # git clone https://github.com/yourusername/codereview-bot.git $APP_DIR
fi

cd $APP_DIR

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your configuration:"
    echo "   nano $APP_DIR/.env"
    echo ""
    echo "Required variables:"
    echo "- BOT_TOKEN: Your Telegram bot token from @BotFather"
    echo "- ADMIN_TG_ID: Your Telegram user ID"
    echo "- DB_PASSWORD: Strong password for PostgreSQL"
fi

# Set up systemd service
echo "🔧 Setting up systemd service..."
cat > /etc/systemd/system/codereview-bot.service << EOF
[Unit]
Description=CodeReview Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable codereview-bot

# Set up firewall
echo "🔥 Configuring firewall..."
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP (if needed)
ufw allow 443/tcp # HTTPS (if needed)
ufw --force enable

echo ""
echo "✅ Server setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano $APP_DIR/.env"
echo "2. Start the bot: cd $APP_DIR && ./scripts/deploy.sh"
echo "3. Or use systemd: systemctl start codereview-bot"
echo "4. View logs: docker-compose logs -f bot"
echo ""
echo "🔒 Security reminder: Change your root password if you haven't already!"