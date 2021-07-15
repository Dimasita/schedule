class Group:
    id: int
    name: str
    faculty: str
    education_type: str
    level: int

    def __init__(self, group_id: int, name: str, faculty: str, education_type: str, level: int):
        self.id = group_id
        self.name = name
        self.faculty = faculty
        self.level = level
        self.education_type = education_type
