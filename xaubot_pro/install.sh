#!/bin/bash

echo "=========================================="
echo "Viral TikTok Bot - Quick Start Installer"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi

echo "✅ Python found"
echo ""

# Install Python dependencies
echo "Installing Python packages..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python packages"
    exit 1
fi

echo "✅ Python packages installed"
echo ""

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Playwright"
    exit 1
fi

echo "✅ Playwright installed"
echo ""

# Check for FFmpeg
echo "Checking for FFmpeg..."
which ffmpeg > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "⚠️  FFmpeg not found. Installing..."
    
    # Try to detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if which brew > /dev/null 2>&1; then
            brew install ffmpeg
        else
            echo "❌ Homebrew not found. Please install FFmpeg manually:"
            echo "   https://ffmpeg.org/download.html"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    else
        echo "❌ Unknown OS. Please install FFmpeg manually:"
        echo "   https://ffmpeg.org/download.html"
    fi
else
    echo "✅ FFmpeg already installed"
fi

echo ""
echo "=========================================="
echo "Installation Complete! 🎉"
echo "=========================================="
echo ""
echo "To start the bot, run:"
echo "  python3 viral_bot.py"
echo ""
echo "Next steps:"
echo "  1. Add your TikTok accounts"
echo "  2. Test login for each account"
echo "  3. Find viral videos"
echo "  4. Start processing!"
echo ""
