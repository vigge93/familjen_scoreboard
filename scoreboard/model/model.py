from flask_sqlalchemy.model import Model


class BaseModel(Model):
    def __eq__(self, other):
        if type(self) != type(other):
            raise TypeError(f"Invalid type: {type(other)}")
        return all(
            (
                getattr(self, c.name) == getattr(other, c.name)
                for c in self.__table__.columns
            )
        )
