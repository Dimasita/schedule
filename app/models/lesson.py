from datetime import time

from models.subject import Subject
from models.teacher import Teacher
from models.group import Group


class Lesson:
    subject: Subject
    teachers: list[Teacher]
    groups: set[Group]
    is_odd_week: bool
    weekday: str
    lesson_number: int
    start_time: str
    end_time: str
    lesson_type: str
    tags: list[{}]
    classrooms: list[{}]

    def __init__(self, subject: Subject, groups: list[Group], teachers: list[Teacher], lesson_number: int,
                 is_odd_week: bool, weekday: str, start_time: time, end_time: time, lesson_type: str,
                 classrooms: list[{}], tags: list[{}]):
        self.teachers = teachers
        self.groups = set(groups)
        self.subject = subject
        self.is_odd_week = is_odd_week
        self.weekday = weekday
        self.lesson_number = lesson_number
        self.start_time = f'{start_time.hour:02d}:{start_time.minute:02d}'
        self.end_time = f'{end_time.hour:02d}:{end_time.minute:02d}'
        self.lesson_type = lesson_type
        self.tags = tags
        self.classrooms = classrooms

    def __hash__(self):
        return hash((
            self.subject.id, self.lesson_number, self.is_odd_week, self.weekday, self.start_time,
            self.end_time, self.lesson_type, self._get_teachers_hash(), self._get_classrooms_hash()
        ))

    def __eq__(self, other):
        if isinstance(other, Lesson):
            return (
                (self.subject.id == other.subject.id) and (self.lesson_number == other.lesson_number) and
                (self.is_odd_week == other.is_odd_week) and (self.weekday == other.weekday) and
                (self.start_time == other.start_time) and (self.end_time == other.end_time) and
                (self.lesson_type == other.lesson_type) and
                (self._get_teachers_hash() == other._get_teachers_hash()) and
                (self._get_classrooms_hash() == other._get_classrooms_hash())
            )
        else:
            return False

    def add_group(self, groups: {Group}) -> None:
        for g in groups:
            self.groups.add(g)

    def to_dict(self):
        d = self.__dict__
        d['teachers'] = [t.__dict__ for t in self.teachers]
        d['groups'] = [g.__dict__ for g in self.groups]
        d['subject'] = self.subject.__dict__
        return d

    def _set_groups_hash(self) -> None:
        self.groups_hash = hash(tuple([obj.id for obj in self.groups]))

    def _get_teachers_hash(self) -> hash:
        return hash(tuple([obj.id for obj in self.teachers]))

    def _get_classrooms_hash(self) -> hash:
        return hash(tuple([obj['name'] for obj in self.classrooms]))
