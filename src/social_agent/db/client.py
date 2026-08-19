from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from social_agent.config import get_settings


@lru_cache
def get_db_client() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(get_settings().mongodb_url)


def get_database() -> AsyncIOMotorDatabase:
    return get_db_client()[get_settings().mongodb_db_name]