#!/bin/bash
# Script to package the bot for deployment

echo "📦 Packaging CodeReview Bot..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create temporary directory
TEMP_DIR="/tmp/codereview-bot-package"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Copy project files
echo "📋 Copying project files..."
cp -r $PROJECT_DIR/* $TEMP_DIR/
cp $PROJECT_DIR/.env.example $TEMP_DIR/
cp $PROJECT_DIR/.gitignore $TEMP_DIR/

# Remove unnecessary files
echo "🗑️  Cleaning up..."
rm -rf $TEMP_DIR/__pycache__
rm -rf $TEMP_DIR/.git
rm -rf $TEMP_DIR/.env
rm -rf $TEMP_DIR/logs
find $TEMP_DIR -name "*.pyc" -delete
find $TEMP_DIR -name ".DS_Store" -delete

# Create archive
ARCHIVE_NAME="codereview-bot-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "📦 Creating archive: $ARCHIVE_NAME"
cd /tmp
tar -czf $PROJECT_DIR/$ARCHIVE_NAME codereview-bot-package/

# Cleanup
rm -rf $TEMP_DIR

echo "✅ Package created: $PROJECT_DIR/$ARCHIVE_NAME"
echo ""
echo "📤 To deploy on server:"
echo "1. Copy to server: scp $ARCHIVE_NAME root@SERVER_IP:/tmp/"
echo "2. On server: cd /opt && tar -xzf /tmp/$ARCHIVE_NAME && mv codereview-bot-package codereview-bot"
echo "3. Follow instructions in QUICK_START.md"