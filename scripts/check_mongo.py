import asyncio
from social_agent.db.client import get_database

async def main():
    db = get_database()
    async for doc in db.pipeline_results.find():
        print(doc.get("repo_name"), doc.get("commit_sha"), doc.get("approval_status"))

asyncio.run(main())