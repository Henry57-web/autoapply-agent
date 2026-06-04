import asyncio

from app.db.session import AsyncSessionLocal
from app.services.legacy_backfill import run_legacy_backfill


async def main() -> None:
    async with AsyncSessionLocal() as db:
        summary = await run_legacy_backfill(db)
    print(summary.render())


if __name__ == "__main__":
    asyncio.run(main())
