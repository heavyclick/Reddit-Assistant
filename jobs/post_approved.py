#!/usr/bin/env python3
"""
Cron job: Post approved drafts to Reddit
Schedule: Every 15 minutes
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reddit_poster import get_reddit_poster


async def main():
    print("=" * 60)
    print("REDDIT POSTING JOB STARTED")
    print("=" * 60)

    try:
        await get_reddit_poster().post_all_approved_drafts()
        print("\n✓ Posting job completed successfully")
    except Exception as e:
        print(f"\n✗ Posting job failed: {e}")
        raise

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
