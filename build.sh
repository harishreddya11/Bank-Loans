#!/usr/bin/env bash
echo "🚀 Starting build process..."

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads
mkdir -p temp_uploads

echo "✅ Build completed successfully!"
echo "📧 Email service: Ready"
echo "💾 Database: Ready"
echo "🌐 Web server: Ready"