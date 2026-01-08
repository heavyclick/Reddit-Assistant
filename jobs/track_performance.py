#!/usr/bin/env python3
"""
Cron job: Track karma performance and generate insights
Schedule: Every 6 hours
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.performance_tracker import get_performance_tracker


async def main():
    print("=" * 60)
    print("PERFORMANCE TRACKING JOB STARTED")
    print("=" * 60)

    try:
        await get_performance_tracker().track_all_accounts()
        print("\n✓ Performance tracking job completed successfully")
    except Exception as e:
        print(f"\n✗ Performance tracking job failed: {e}")
        raise

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
