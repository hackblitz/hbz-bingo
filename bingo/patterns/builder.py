from typing import Dict


class BuilderMeta(type):
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        required_attributes = []

        if "attributes" not in attrs:
            raise Exception(
                f"Unable to create builder {name} due to missing attributes"
            )

        for attribute, meta in attrs["attributes"].items():
            if "required" not in meta or "type" not in meta:
                raise Exception(
                    f"Unable to create builder class, Invalid attribute ({attribute} -> {str(meta)})"
                )

            if meta["required"]:
                required_attributes.append(attribute)

        setattr(cls, "__required_attributes__", required_attributes)
        return cls


class Builder(metaclass=BuilderMeta):
    """
    Parent class to make a class builder.

    Implementation:
        class LogBuilder(Builder):
            attributes = {
                "level": {
                    "required": True,
                    "type": str
                }
            }

            def __build__(self):
                log = logging.getLogger('root')
                log.setLevel(self.level)
                return log

        log = LogBuilder().set("level", "info").build()
    """

    attributes: Dict[str, Dict[str, any]] = {}

    def __build__(self):
        """
        Implement this method in the actual builder class. This method
        should return the output of the build.
        """

        raise NotImplementedError(
            f"__build__ is not implemented in {self.__class__.__name__}"
        )

    def set(self, attribute: str, value: any) -> object:
        """
        Set a value for attribute in the class.
        """

        if attribute in self.attributes:
            _type = self.attributes[attribute].get("type", str)

            if not isinstance(value, _type):
                raise TypeError(f"{value} is not a {str(_type)}")

            setattr(self, attribute, value)
            return self

        raise ValueError(f"{attribute} is unexpected for {self.__class__.__name__}")

    def build(self):
        for attribute in self.__required_attributes__:
            if not hasattr(self, attribute):
                raise AttributeError(
                    f"Required attribute {attribute} not found. Use .set() to set the attribute."
                )
        return self.__build__()
