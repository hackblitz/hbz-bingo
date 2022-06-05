import logging

from motor.motor_asyncio import AsyncIOMotorClient


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def get_database() -> AsyncIOMotorClient:
    return db.client


async def connect(mongo_url):
    """
    Connect to mongodb
    """

    db.client = AsyncIOMotorClient(str(mongo_url))
    logging.info(f"Connected to mongodb at {mongo_url}")


async def close():
    """
    Disconnect from mongodb
    """

    db.client.close()
    logging.info("Disconnected from mongodb")
