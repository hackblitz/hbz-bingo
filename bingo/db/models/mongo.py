from datetime import datetime, timezone
from typing import Optional

from bingo.db.exceptions import IntegrityError
from bingo.db.fields import Field
from bingo.db.models import BaseConfig, BaseModel
from bingo.typing import Identifier
from bson import ObjectId


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
    Model manager class for mongodb.
    This will be available in the objects attribute in the MongoModel.
    """

    def __init__(self, model_class):
        self.model_class = model_class

    async def get_collection(self):
        """
        Collection on which this model interacts.
        """
        from bingo.db.mongo import AsyncIOMotorClient, get_client, get_database

        client: AsyncIOMotorClient = await get_client()
        return client[get_database()][self.model_class.get_collection_name()]

    async def get(self, **attributes):
        """
        Gets a document from the collection with attributes.
        """

        collection = await self.get_collection()
        id = attributes.get("id")

        if id:
            del attributes["id"]
            attributes["_id"] = Identifier(id)

        obj = await collection.find_one(attributes)

        if obj:
            return self.model_class(**obj)

    async def filter(self, **attributes):
        """
        Gets multiple documents from the collection with attributes.
        """

        collection = await self.get_collection()
        objs = collection.find(attributes)

        if objs:
            return [self.model_class(**obj) async for obj in objs]

    async def create(self, **attributes):
        """
        Creates a document in the collection.
        """

        obj = self.model_class(**attributes)

        if hasattr(self.model_class, "Meta"):
            if hasattr(self.model_class.Meta, "unique_together"):
                duplicate_kwargs = {}

                for field in self.model_class.Meta.unique_together:
                    if field in attributes:
                        duplicate_kwargs[field] = attributes[field]

                if len(duplicate_kwargs) == len(
                    self.model_class.Meta.unique_together
                ) and await self.get(**duplicate_kwargs):
                    raise IntegrityError(duplicate_kwargs)
            elif hasattr(self.model_class.Meta, "unique"):
                if await self.get(
                    **{
                        self.model_class.Meta.unique: attributes[
                            self.model_class.Meta.unique
                        ]
                    }
                ):
                    raise IntegrityError(
                        {
                            self.model_class.Meta.unique: attributes[
                                self.model_class.Meta.unique
                            ]
                        }
                    )

        collection = await self.get_collection()
        obj.last_updated = datetime.now()

        if hasattr(obj, "id"):
            delattr(obj, "id")

        new_obj = await collection.insert_one(obj.dict(by_alias=True))

        if new_obj:
            return str(new_obj.inserted_id)

    async def count(self, **attributes):
        """
        Total number of objects in a collection based on attributes.
        """

        collection = await self.get_collection()
        return await collection.count_documents(attributes)


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
        allow_population_by_alias = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            Identifier: str,
            ObjectId: str,
        }

    @classmethod
    def get_collection_name(cls) -> str:
        """
        Collection name on which this model interacts.
        """

        return f"{cls.__name__.lower()}s"
