from enum import IntFlag, auto, unique


@unique
class ClearanceEnum(IntFlag):
    User = auto()
    Admin = auto()
    Wannabe = auto()
