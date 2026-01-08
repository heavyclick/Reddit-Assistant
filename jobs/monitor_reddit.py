#!/usr/bin/env python3
"""
Cron job: Monitor Reddit for karma opportunities
Schedule: Every 30 minutes
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reddit_monitor import reddit_monitor


async def main():
    print("=" * 60)
    print("REDDIT MONITORING JOB STARTED")
    print("=" * 60)

    try:
        await reddit_monitor.monitor_all_accounts()
        print("\n✓ Monitoring job completed successfully")
    except Exception as e:
        print(f"\n✗ Monitoring job failed: {e}")
        raise

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
