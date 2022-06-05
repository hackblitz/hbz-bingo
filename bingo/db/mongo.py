import logging

from motor.motor_asyncio import AsyncIOMotorClient


class Database:
    client: AsyncIOMotorClient = None
    database: str = None


db = Database()


async def get_client() -> AsyncIOMotorClient:
    return db.client


def get_database() -> str:
    return db.database


async def connect(mongo_url: str, database: str = "bingo"):
    """
    Connect to mongodb
    """

    db.client = AsyncIOMotorClient(str(mongo_url))
    db.database = database
    logging.info(f"Connected to mongodb at {mongo_url}")


async def close():
    """
    Disconnect from mongodb
    """

    db.client.close()
    logging.info("Disconnected from mongodb")
