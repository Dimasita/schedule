from datetime import time

from models.subject import Subject
from models.teacher import Teacher
from models.group import Group


class Lesson:
    subject: Subject
    teachers: list[Teacher]
    groups: list[Group]
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
        self.groups = groups
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
        return hash((self.subject.id, self.lesson_number, self.is_odd_week, self.weekday,
                     self.start_time, self.end_time, self.lesson_type, self._hash_groups(),
                     self._hash_groups(), self._hash_classrooms()))

    def to_dict(self):
        d = self.__dict__
        d['teachers'] = [t.__dict__ for t in self.teachers]
        d['groups'] = [g.__dict__ for g in self.groups]
        d['subject'] = self.subject.__dict__
        return d

    def _hash_groups(self) -> hash:
        return hash(tuple([obj.id for obj in self.groups]))

    def _hash_teachers(self) -> hash:
        return hash(tuple([obj.id for obj in self.teachers]))

    def _hash_classrooms(self) -> hash:
        return hash(tuple([obj['name'] for obj in self.classrooms]))
