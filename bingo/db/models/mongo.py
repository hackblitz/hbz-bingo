from datetime import datetime, timezone
from typing import Optional

from bingo.db.exceptions import IntegrityError
from bingo.db.fields import Field
from bingo.db.models import BaseConfig, BaseModel
from bingo.types import Identifier


def __metaclass_resolver__(*classes):
    metaclass = tuple(set(type(cls) for cls in classes))
    metaclass = (
        metaclass[0]
        if len(metaclass) == 1
        else type("_".join(mcls.__name__ for mcls in metaclass), metaclass, {})
    )
    return metaclass("_".join(cls.__name__ for cls in classes), classes, {})


class MongoModelManager:
    """
    Model manager class for mongodb. This will be available in the objects attribute in the MongoModel.
    """

    def __init__(self, model_class):
        self.model_class = model_class

    async def get_collection(self):
        from bingo.db.mongo import AsyncIOMotorClient, get_client, get_database

        client: AsyncIOMotorClient = await get_client()
        return client[get_database()][self.model_class.get_collection_name()]

    async def get(self, **kwargs):
        """
        Find one document from the collection with the given kwargs
        """

        collection = await self.get_collection()
        id = kwargs.get("id")

        if id:
            del kwargs["id"]
            kwargs["_id"] = Identifier(id)

        obj = await collection.find_one(kwargs)

        if obj:
            return self.model_class(**obj)

    async def filter(self, **kwargs):
        """
        Find multiple documents from the collection with the given kwargs
        """

        collection = await self.get_collection()
        objs = collection.find(kwargs)

        if objs:
            return [self.model_class(**obj) async for obj in objs]

    async def create(self, **kwargs):
        """
        Create document in the collection with given kwargs
        """

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
                    raise IntegrityError(
                        f"Duplicate element found with identifier {str(duplicate_kwargs)}"
                    )
            elif hasattr(self.model_class.Meta, "unique"):
                if await self.get(
                    **{
                        self.model_class.Meta.unique: kwargs[
                            self.model_class.Meta.unique
                        ]
                    }
                ):
                    raise IntegrityError(
                        f"Duplicate element found with identifier {str({self.model_class.Meta.unique: kwargs[self.model_class.Meta.unique]})}"
                    )

        collection = await self.get_collection()
        obj.last_updated = datetime.now()

        if hasattr(obj, "id"):
            delattr(obj, "id")

        new_obj = await collection.insert_one(obj.dict(by_alias=True))

        if new_obj:
            return str(new_obj.inserted_id)

    async def count(self, **kwargs):
        """
        Number of documents in the collection with the given kwargs
        """

        collection = await self.get_collection()
        return await collection.count_documents(kwargs)


class MongoObjectMeta(type):
    def __new__(mcs, *args, **kwargs):
        cls = super().__new__(mcs, *args, **kwargs)
        setattr(cls, "objects", MongoModelManager(cls))
        return cls


class MongoModelMeta(object, metaclass=MongoObjectMeta):
    pass


class MongoModel(__metaclass_resolver__(BaseModel, MongoModelMeta)):
    """
    Base model class for mongodb
    """

    id: Optional[Identifier] = Field(alias="_id")
    last_updated: datetime = Field(default=None, alias="_last_updated")

    class Config(BaseConfig):
        from bson import ObjectId

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
        """
        Collection on which the model with query upon
        """

        return f"{cls.__name__.lower()}s"
