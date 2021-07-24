from typing import Optional


class Group:
    id: int
    name: str
    faculty: Optional[str]
    education_type: Optional[str]
    level: Optional[int]

    def __init__(self, group_id: int, name: str, faculty: str = None,
                 education_type: str = None, level: int = None):
        self.id = int(group_id)
        self.name = name
        self.faculty = faculty
        self.level = level
        self.education_type = education_type

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, Group):
            return self.id == other.id
        else:
            return False
