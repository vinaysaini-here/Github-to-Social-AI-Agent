import asyncio
from social_agent.db.client import get_database

async def main():
    db = get_database()
    doc = await db.github_users.find_one({})
    print(doc)

asyncio.run(main())