from datetime import datetime, timezone
from typing import Optional

from bingo.db.fields import Field
from bingo.db.models import BaseConfig, BaseModel
from bingo.types import Identifier
from bson import ObjectId


def _metaclass_resolver(*classes):
    metaclass = tuple(set(type(cls) for cls in classes))
    metaclass = (
        metaclass[0]
        if len(metaclass) == 1
        else type("_".join(mcls.__name__ for mcls in metaclass), metaclass, {})
    )
    return metaclass("_".join(cls.__name__ for cls in classes), classes, {})


class MongoModelManager:
    def __init__(self, model_class):
        self.model_class = model_class

    async def get_collection(self):
        from bingo.db.mongo import AsyncIOMotorClient, get_database

        connection: AsyncIOMotorClient = await get_database()
        return connection["questions"][self.model_class.get_collection_name()]

    async def get(self, **kwargs):
        collection = await self.get_collection()
        id = kwargs.get("id")

        if id:
            del kwargs["id"]
            kwargs["_id"] = Identifier(id)

        obj = await collection.find_one(kwargs)

        if obj:
            return self.model_class(**obj)

    async def filter(self, **kwargs):
        collection = await self.get_collection()
        objs = collection.find(kwargs)

        if objs:
            return [self.model_class(**obj) async for obj in objs]

    async def create(self, **kwargs):
        obj = self.model_class(**kwargs)

        if hasattr(self.model_class, "Meta"):
            if hasattr(self.model_class.Meta, "unique_together"):
                duplicate_kwargs = {}

                for field in self.model_class.Meta.unique_together:
                    if field in kwargs:
                        duplicate_kwargs[field] = kwargs[field]

                if len(duplicate_kwargs) == len(
                    self.model_class.Meta.unique_together
                ) and await self.get(**duplicate_kwargs):
                    raise Exception("Integrity error")
            elif hasattr(self.model_class.Meta, "unique"):
                if await self.get(
                    **{
                        self.model_class.Meta.unique: kwargs[
                            self.model_class.Meta.unique
                        ]
                    }
                ):
                    raise Exception("Integrity error")

        collection = await self.get_collection()
        obj.last_updated = datetime.now()

        if hasattr(obj, "id"):
            delattr(obj, "id")

        new_obj = await collection.insert_one(obj.dict(by_alias=True))

        if new_obj:
            return str(new_obj.inserted_id)

    async def count(self, **kwargs):
        collection = await self.get_collection()
        return await collection.count_documents(kwargs)


class MongoObjectMeta(type):
    def __new__(mcs, *args, **kwargs):
        cls = super().__new__(mcs, *args, **kwargs)
        setattr(cls, "objects", MongoModelManager(cls))
        return cls


class MongoModelMeta(object, metaclass=MongoObjectMeta):
    pass


class MongoModel(_metaclass_resolver(BaseModel, MongoModelMeta)):

    id: Optional[Identifier] = Field(alias="_id")
    last_updated: datetime = Field(default=None, alias="_last_updated")

    class Config(BaseConfig):
        allow_population_by_alias = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            Identifier: str,
            ObjectId: str,
        }

    @classmethod
    def get_collection_name(cls):
        return f"{cls.__name__.lower()}s"
