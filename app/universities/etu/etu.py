import json
from datetime import time, datetime

from models.group import Group
from models.lesson import Lesson
from models.subject import Subject
from models.teacher import Teacher
from universities.university import University
from services.helper import humanize_weekday, get_correct_lesson_type
from services.requests import get_json
from universities.etu.config import LINK
from services.decorators import benchmark


class Etu(University):
    full_data: json

    @benchmark('import')
    def __init__(self):
        self.full_data = get_json(LINK, 'GET')

    @benchmark('set groups')
    def _set_groups(self) -> None:
        for g in self.full_data:
            if g['groupSets'] is None or len(g['groupSets']) == 0:
                title = g['fullNumber']
            else:
                title = g['groupSets'][0]['title']
            self.groups[g['id']] = Group(
                g['id'],
                g['number'],
                title,
                g['studyingType'],
                g['course']
            )

    @benchmark('set subjects')
    def _set_subjects(self) -> None:
        for g in self.full_data:
            if g['scheduleObjects'] is not None:
                for s in g['scheduleObjects']:
                    if s['lesson']['subject']['id'] not in self.subjects.keys():
                        self.subjects[s['lesson']['subject']['id']] = Subject(s['lesson']['subject']['title'])

    @benchmark('set teachers')
    def _set_teachers(self) -> None:
        for g in self.full_data:
            if g['scheduleObjects'] is not None:
                for s in g['scheduleObjects']:
                    if s['lesson']['teacher'] is not None:
                        if s['lesson']['teacher']['id'] not in self.teachers.keys():
                            self.teachers[s['lesson']['teacher']['id']] = Teacher(
                                s['lesson']['teacher']['id'],
                                s['lesson']['teacher']['initials'],
                                s['lesson']['teacher']['position'],
                                s['lesson']['teacher']['alienId']
                            )
                    if s['lesson']['secondTeacher'] is not None:
                        if s['lesson']['secondTeacher']['id'] not in self.teachers.keys():
                            self.teachers[s['lesson']['secondTeacher']['id']] = Teacher(
                                s['lesson']['secondTeacher']['id'],
                                s['lesson']['secondTeacher']['initials'],
                                s['lesson']['secondTeacher']['position'],
                                s['lesson']['secondTeacher']['alienId']
                            )

    @benchmark('set lessons')
    def _set_lessons(self) -> None:
        for g in self.full_data:
            if g['scheduleObjects'] is not None:
                for s in g['scheduleObjects']:
                    teachers = list()
                    groups = list()
                    tags = list()
                    classrooms = list()
                    if s['lesson']['teacher'] is not None:
                        teachers.append(self.teachers[s['lesson']['teacher']['id']])
                    if s['lesson']['secondTeacher'] is not None:
                        teachers.append(self.teachers[s['lesson']['secondTeacher']['id']])
                    if int(s['lesson']['auditoriumReservation']['reservationTime']['week']) % 2 == 1:
                        is_odd_week = False
                    else:
                        is_odd_week = True
                    start_time = s['lesson']['auditoriumReservation']['reservationTime']['startTime']
                    end_time = s['lesson']['auditoriumReservation']['reservationTime']['endTime']
                    classroom = {'building': None}
                    if s['isDistant']:
                        classroom['name'] = 'Дистанционно'
                    else:
                        classroom['name'] = s['lesson']['auditoriumReservation']['auditoriumNumber']
                    classrooms.append(classroom)
                    if s['url'] is not None:
                        tags.append({'text': '', 'link': s['url'], 'type': 'blue'})
                    groups.append(self.groups[int(s['groupId'])])
                    self.lessons.add(
                        Lesson(
                            self.subjects[int(s['lesson']['subject']['id'])],
                            groups,
                            teachers,
                            self._calculate_lesson_number(start_time, end_time),
                            is_odd_week,
                            humanize_weekday(s['lesson']['auditoriumReservation']['reservationTime']['weekDay']),
                            self._calculate_start_time(start_time),
                            self._calculate_end_time(end_time),
                            get_correct_lesson_type(s['lesson']['subject']['subjectType']),
                            classrooms,
                            tags
                        )
                    )

    @staticmethod
    def _calculate_start_time(start_time: str) -> time:
        # :TODO
        return datetime.strptime('00:00', '%H:%M').time()

    @staticmethod
    def _calculate_end_time(end_time: str) -> time:
        # :TODO
        return datetime.strptime('00:00', '%H:%M').time()

    @staticmethod
    def _calculate_lesson_number(start_time: int, end_time: int) -> int:
        table = {
            8: 1,
            10: 2,
            12: 3,
            14: 4,
            16: 5,
            18: 6,
            20: 7
        }
        hours = start_time
        if hours not in table.keys():
            return 0
        return table[hours]
