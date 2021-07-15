from typing import Optional


class Teacher:
    id: int
    full_name: str
    position: Optional[str]
    oid: Optional[int]   # апи политеха возвращает, мб где-то нужно

    def __init__(self, teacher_id: int, full_name: str, position: str = None, oid: int = None):
        self.id = teacher_id
        self.full_name = full_name
        self.position = position
        self.oid = oid
