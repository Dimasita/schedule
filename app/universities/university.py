import json

from models.group import Group
from models.subject import Subject
from models.teacher import Teacher
from models.lesson import Lesson
from services.decorators import benchmark


class University:
    groups: {int: Group} = dict()
    teachers: {int: Teacher} = dict()
    subjects: {str: Subject} = dict()
    schedule: [] = list()
    lessons: [Lesson] = set()

    @benchmark('total')
    def set_default_values(self) -> None:
        self._set_groups()
        self._set_teachers()
        self._set_subjects()
        self._set_lessons()

    def set_values_from_file(self, data: json) -> None:
        if 'groups' not in data.keys() or data['groups'] is None or len(data['groups']) == 0:
            self._set_groups()
        else:
            for g in data['groups']:
                self.groups[g['id']] = Group(g['id'], g['name'], g['faculty'], g['education_type'], g['level'])
        if 'teachers' not in data.keys() or data['teachers'] is None or len(data['teachers']) == 0:
            self._set_teachers()
        else:
            for t in data['teachers']:
                self.teachers[t['id']] = Teacher(t['id'], t['full_name'], t['position'], t['oid'])
        if 'subjects' not in data.keys() or data['subjects'] is None or len(data['subjects']) == 0:
            self._set_subjects()
        else:
            for s in data['subjects']:
                self.subjects[s['id']] = Subject(s['name'])
        self._set_lessons()

    def get_values(self) -> {str: []}:
        return {
            'groups': [obj.__dict__ for obj in self.groups.values()],
            'teachers': [obj.__dict__ for obj in self.teachers.values()],
            'subjects': [obj.__dict__ for obj in self.subjects.values()],
            'lessons': [obj.to_dict() for obj in self.lessons]
        }

    def _add_lesson(self, lesson: Lesson) -> None:
        if lesson not in self.lessons:
            self.lessons.add(lesson)
            return
        for lsn in self.lessons:
            if lsn == lesson:
                lsn.add_group(lesson.groups)
                break

    def _set_groups(self) -> None:
        raise NotImplementedError

    def _set_subjects(self) -> None:
        raise NotImplementedError

    def _set_teachers(self) -> None:
        raise NotImplementedError

    def _set_lessons(self) -> None:
        raise NotImplementedError
