#!/bin/bash

# Vercel Deployment Helper Script

set -e

echo "🚀 Vercel Deployment Helper"
echo "============================="
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed."
    echo "Install it with: npm i -g vercel"
    exit 1
fi

echo "✓ Vercel CLI found"
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cat > .env << EOF
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
CHAT_ID=your_chat_id
TIMEZONE=Europe/Warsaw
CRON_SECRET=$(openssl rand -hex 32)
EOF
    echo "✓ Created .env file. Please edit it with your values."
    echo ""
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check BOT_TOKEN
if [ "$BOT_TOKEN" = "your_bot_token_here" ] || [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN not set in .env"
    echo "Get it from @BotFather on Telegram"
    exit 1
fi

echo "✓ BOT_TOKEN configured"

# Deploy to Vercel
echo ""
echo "📦 Deploying to Vercel..."
echo ""

if vercel --prod; then
    echo ""
    echo "✓ Deployment successful!"
    echo ""
    
    # Get the deployment URL
    VERCEL_URL=$(vercel ls --prod | grep -m 1 "komanda-telegram" | awk '{print $2}')
    
    if [ -z "$VERCEL_URL" ]; then
        echo "⚠️  Could not automatically detect Vercel URL."
        echo "Please run manually:"
        echo "  python scripts/set_webhook.py https://your-app.vercel.app"
    else
        echo "🔗 Your app URL: https://$VERCEL_URL"
        echo ""
        echo "Setting up webhook..."
        
        if python scripts/set_webhook.py "https://$VERCEL_URL"; then
            echo ""
            echo "✅ Webhook configured successfully!"
            echo ""
            echo "📋 Next steps:"
            echo "1. Test your bot by sending a message"
            echo "2. Set up cron jobs at https://cron-job.org"
            echo "   - Open sessions: https://$VERCEL_URL/api/cron?task=open_sessions&secret=$CRON_SECRET"
            echo "   - Send reminders: https://$VERCEL_URL/api/cron?task=send_reminders&secret=$CRON_SECRET"
            echo "   - Close sessions: https://$VERCEL_URL/api/cron?task=close_sessions&secret=$CRON_SECRET"
            echo ""
            echo "📖 Full documentation: DEPLOYMENT.md"
        else
            echo ""
            echo "❌ Failed to set webhook. Try manually:"
            echo "  python scripts/set_webhook.py https://$VERCEL_URL"
        fi
    fi
else
    echo ""
    echo "❌ Deployment failed. Check the errors above."
    exit 1
fi
