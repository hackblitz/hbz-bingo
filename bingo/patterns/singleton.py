class Singleton(type):
    """
    Metaclass to make a class singleton. Singleton ensures only one
    object is created for the class.

    Implementation:
        class Logger(metaclass=Singleton):
            pass
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]
