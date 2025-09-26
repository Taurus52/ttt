#!/bin/bash
# Deployment script for CodeReview Bot

set -e

echo "🚀 Starting CodeReview Bot deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file based on .env.example"
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
required_vars=("BOT_TOKEN" "ADMIN_TG_ID" "DB_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env file!"
        exit 1
    fi
done

# Create logs directory
mkdir -p logs

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Check service status
echo "✅ Checking service status..."
docker-compose ps

echo "🎉 Deployment complete!"
echo ""
echo "📊 Services:"
echo "- Bot: Running"
echo "- PostgreSQL: localhost:5432"
echo "- Adminer: http://localhost:8080"
echo ""
echo "📝 View logs:"
echo "docker-compose logs -f bot"