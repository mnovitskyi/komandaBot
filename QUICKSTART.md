# Quick Start - Vercel Deployment

## 1️⃣ Prerequisites

- [ ] GitHub account
- [ ] Vercel account (free): https://vercel.com
- [ ] Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- [ ] PostgreSQL database (free options below)

### Get a Free PostgreSQL Database

**Option A: Supabase (Recommended)**
1. Go to https://supabase.com
2. Create new project
3. Copy the "Connection pooling" URL from Settings → Database
4. Use this as your `DATABASE_URL`

**Option B: Neon**
1. Go to https://neon.tech
2. Create new project
3. Copy the connection string
4. Use this as your `DATABASE_URL`

## 2️⃣ Deploy in 3 Steps

### Step 1: Fork/Clone This Repo

```bash
git clone https://github.com/yourusername/komanda-telegram.git
cd komanda-telegram
```

### Step 2: Deploy to Vercel

**Method A: Using Vercel Dashboard (Easiest)**
1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Set environment variables:
   - `BOT_TOKEN` = Your bot token from @BotFather
   - `DATABASE_URL` = Your PostgreSQL connection string
   - `CHAT_ID` = Your Telegram chat ID (optional)
   - `TIMEZONE` = Europe/Warsaw (or your timezone)
   - `CRON_SECRET` = Generate random string (e.g., `openssl rand -hex 32`)
4. Click Deploy

**Method B: Using CLI**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

### Step 3: Set Webhook

After deployment, get your Vercel URL (e.g., `https://your-app.vercel.app`) and run:

```bash
# Make sure you have the dependencies installed
pip install -r requirements.txt

# Set the webhook
python scripts/set_webhook.py https://your-app.vercel.app
```

✅ **Test your bot!** Send it a message on Telegram.

## 3️⃣ Setup Scheduled Tasks (Optional but Recommended)

Your bot needs scheduled tasks to automatically open/close booking sessions. Use a free cron service:

### Using cron-job.org (Free)

1. Go to https://cron-job.org and sign up
2. Create 3 cron jobs:

**Job 1: Open Sessions (Thursday 18:00)**
- URL: `https://your-app.vercel.app/api/cron?task=open_sessions&secret=YOUR_CRON_SECRET`
- Schedule: `0 18 * * 4` (Thursday at 18:00)

**Job 2: Send Reminders (Saturday & Sunday, 1 hour before game)**
- URL: `https://your-app.vercel.app/api/cron?task=send_reminders&secret=YOUR_CRON_SECRET`
- Schedule: Adjust based on your typical game times

**Job 3: Close Sessions (Sunday 23:00)**
- URL: `https://your-app.vercel.app/api/cron?task=close_sessions&secret=YOUR_CRON_SECRET`
- Schedule: `0 23 * * 0` (Sunday at 23:00)

Replace `YOUR_CRON_SECRET` with the value you set in Vercel environment variables.

## 4️⃣ Get Your Chat ID

1. Add your bot to your Telegram group
2. Make the bot an admin (so it can delete messages)
3. Send `/chatid` in the group
4. Copy the ID and add it to Vercel environment variables:
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add/update `CHAT_ID` with your chat ID
   - Redeploy: `vercel --prod`

## 🎉 Done!

Your bot is now live! Try these commands:
- `/help` - See all commands
- `/status` - View current bookings
- `/book` - Book a slot

## 📊 Monitor Your Bot

```bash
# View real-time logs
vercel logs --follow

# Check deployment status
vercel ls
```

## 🐛 Troubleshooting

### Bot not responding
```bash
# Check logs
vercel logs

# Verify webhook
python scripts/set_webhook.py https://your-app.vercel.app
```

### Database connection errors
- Ensure DATABASE_URL is correct
- For Supabase: Use the "connection pooling" URL, not direct connection
- Check if your database allows external connections

### Webhook verification failed
```bash
# Delete and reset webhook
python scripts/set_webhook.py --delete
python scripts/set_webhook.py https://your-app.vercel.app
```

## 🔄 Switching Back to Local Development

```bash
# Remove webhook
python scripts/set_webhook.py --delete

# Run locally with polling
python -m bot.main
```

## 💰 Costs

- **Vercel**: Free (10K webhook calls/month)
- **Supabase/Neon**: Free tier (500MB-1GB)
- **Cron-job.org**: Free (up to 50 jobs)

**Total: $0/month** ✨

## 📚 More Info

- [Full Deployment Guide](DEPLOYMENT.md)
- [Project README](README.md)
