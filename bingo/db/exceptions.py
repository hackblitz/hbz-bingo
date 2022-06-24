class IntegrityError(Exception):
    def __init__(self, attributes: any) -> None:
        super().__init__(f"Duplicate element found with identifier {str(attributes)}")
