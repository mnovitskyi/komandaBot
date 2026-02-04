"""
Test Vercel deployment endpoints.
Usage: python scripts/test_vercel.py https://your-app.vercel.app
"""
import sys
import asyncio
import aiohttp


async def test_webhook(url: str):
    """Test webhook endpoint."""
    webhook_url = f"{url}/api/webhook"
    
    print(f"Testing webhook: {webhook_url}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(webhook_url, timeout=10) as resp:
                status = resp.status
                text = await resp.text()
                
                if status == 200:
                    print(f"✓ Webhook is accessible (Status: {status})")
                    print(f"  Response: {text[:100]}")
                    return True
                else:
                    print(f"✗ Webhook returned status {status}")
                    print(f"  Response: {text[:200]}")
                    return False
        except asyncio.TimeoutError:
            print("✗ Webhook timeout (10s)")
            return False
        except Exception as e:
            print(f"✗ Webhook error: {e}")
            return False


async def test_cron(url: str, secret: str = None):
    """Test cron endpoint."""
    cron_url = f"{url}/api/cron"
    if secret:
        cron_url += f"?task=open_sessions&secret={secret}"
    
    print(f"\nTesting cron: {cron_url.split('?')[0]}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(cron_url, timeout=10) as resp:
                status = resp.status
                text = await resp.text()
                
                if status in [200, 400, 401]:  # These are expected
                    print(f"✓ Cron endpoint is accessible (Status: {status})")
                    print(f"  Response: {text[:200]}")
                    return True
                else:
                    print(f"✗ Cron returned unexpected status {status}")
                    return False
        except asyncio.TimeoutError:
            print("✗ Cron timeout (10s)")
            return False
        except Exception as e:
            print(f"✗ Cron error: {e}")
            return False


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_vercel.py <vercel-url> [cron-secret]")
        print("Example: python scripts/test_vercel.py https://your-app.vercel.app")
        sys.exit(1)
    
    url = sys.argv[1].rstrip("/")
    secret = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("=" * 50)
    print("Vercel Deployment Test")
    print("=" * 50)
    print(f"URL: {url}\n")
    
    webhook_ok = await test_webhook(url)
    cron_ok = await test_cron(url, secret)
    
    print("\n" + "=" * 50)
    if webhook_ok and cron_ok:
        print("✅ All tests passed!")
        print("\nNext steps:")
        print("1. Set webhook: python scripts/set_webhook.py", url)
        print("2. Test your bot by sending a message")
        print("3. Set up cron jobs at https://cron-job.org")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("- Ensure environment variables are set in Vercel")
        print("- Check Vercel deployment logs: vercel logs")
        print("- Verify your BOT_TOKEN and DATABASE_URL are correct")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
