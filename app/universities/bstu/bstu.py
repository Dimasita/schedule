import re
import xmltodict
from datetime import time, timedelta, datetime, date

from models.group import Group
from models.lesson import Lesson
from models.subject import Subject
from models.teacher import Teacher
from universities.university import University
from services.helper import humanize_weekday, get_correct_lesson_type
from services.requests import get_xml
from universities.bstu.config import LINK
from services.decorators import benchmark


class Bstu(University):
    full_data: xmltodict

    @benchmark('import')
    def __init__(self):
        self.full_data = get_xml(LINK['FULL'], 'GET')

    @benchmark('set groups')
    def _set_groups(self) -> None:
        for g in self.full_data['Timetable']['Group']:
            g_id = int(g['@IdGroup'])
            if g_id not in self.groups.keys():
                self.groups[g_id] = Group(g_id, g['@Number'])

    @benchmark('set teachers')
    def _set_teachers(self) -> None:
        for g in self.full_data['Timetable']['Group']:
            if 'Days' in g.keys() and 'Day' in g['Days'].keys() and g['Days']['Day'] is not None:
                for d in g['Days']['Day']:
                    if ('GroupLessons' in d.keys() and
                        'Lesson' in d['GroupLessons'].keys()
                        and d['GroupLessons']['Lesson'])\
                            is not None:
                        if type(d['GroupLessons']['Lesson']) != list:
                            lst = d['GroupLessons']['Lesson']
                            d['GroupLessons']['Lesson'] = list()
                            d['GroupLessons']['Lesson'].append(lst)
                        for lesson in d['GroupLessons']['Lesson']:
                            if 'Lecturers' in lesson.keys() and lesson['Lecturers'] is not None:
                                if type(lesson['Lecturers']['Lecturer']) is list:
                                    for teacher in lesson['Lecturers']['Lecturer']:
                                        t_id = int(teacher['IdLecturer'])
                                        if t_id not in self.teachers.keys():
                                            self.teachers[t_id] = Teacher(t_id, teacher['ShortName'])
                                else:
                                    t_id = int(lesson['Lecturers']['Lecturer']['IdLecturer'])
                                    if t_id not in self.teachers.keys():
                                        self.teachers[t_id] = Teacher(
                                            t_id,
                                            lesson['Lecturers']['Lecturer']['ShortName']
                                        )

    def _set_subjects(self) -> None:
        pass

    @benchmark('set lessons')
    def _set_lessons(self) -> None:
        for g in self.full_data['Timetable']['Group']:
            if 'Days' in g.keys() and 'Day' in g['Days'].keys() and g['Days']['Day'] is not None:
                for d in g['Days']['Day']:
                    if ('GroupLessons' in d.keys() and
                        'Lesson' in d['GroupLessons'].keys()
                        and d['GroupLessons']['Lesson'])\
                            is not None:
                        if type(d['GroupLessons']['Lesson']) != list:
                            lst = d['GroupLessons']['Lesson']
                            d['GroupLessons']['Lesson'] = list()
                            d['GroupLessons']['Lesson'].append(lst)
                        for lesson in d['GroupLessons']['Lesson']:
                            teachers = list()
                            groups = list()
                            tags = list()
                            classrooms = list()
                            if 'Lecturers' in lesson.keys() and lesson['Lecturers'] is not None:
                                if type(lesson['Lecturers']['Lecturer']) is list:
                                    for teacher in lesson['Lecturers']['Lecturer']:
                                        teachers.append(self.teachers[int(teacher['IdLecturer'])])
                                else:
                                    teachers.append(self.teachers[int(lesson['Lecturers']['Lecturer']['IdLecturer'])])
                            groups.append(self.groups[int(g['@IdGroup'])])
                            lesson_type, subject_name = self._parse_subject(lesson['Discipline'])
                            subject = Subject(subject_name)
                            if subject.id not in self.subjects.keys():
                                self.subjects[subject.id] = subject
                            else:
                                subject = self.subjects[subject.id]
                            if lesson['Classroom'] is not None:
                                classroom = lesson['Classroom'].replace(';', '')
                                if '*' in classroom:
                                    classrooms.append({
                                        'name': classroom.replace('*', ''),
                                        'building': 'УЛК - 1-ая Красноармейская, д. 13'
                                    })
                                else:
                                    classrooms.append({
                                        'name': classroom,
                                        'building': '1-ая Красноармейская, д. 13'
                                    })
                            if int(lesson['WeekCode']) % 2 == 1:
                                is_odd_week = False
                            else:
                                is_odd_week = True
                            start_time = self._get_start_time(lesson['Time'])
                            end_time = self._get_end_time(start_time)
                            self._add_lesson(
                                Lesson(
                                    subject,
                                    groups,
                                    teachers,
                                    self._calculate_lesson_number(start_time.hour),
                                    is_odd_week,
                                    humanize_weekday(lesson['DayTitle']),
                                    start_time,
                                    end_time,
                                    lesson_type,
                                    classrooms,
                                    tags
                                )
                            )

    @staticmethod
    def _get_start_time(value: str) -> (str, str):
        return datetime.strptime(re.findall(r'(\d+:\d+) ', value)[0], '%H:%M').time()

    @staticmethod
    def _get_end_time(value: time) -> (str, str):
        return (datetime.combine(date(1, 1, 1), value) + timedelta(hours=1, minutes=30)).time()

    @staticmethod
    def _calculate_lesson_number(start_time: int) -> int:
        table = {
            9: 1,
            10: 2,
            12: 3,
            14: 4,
            16: 5
        }
        hours = start_time
        if hours not in table.keys():
            return 0
        return table[hours]

    @staticmethod
    def _parse_subject(subject: str) -> (str, str):
        subject = subject.split(' ')
        lesson_type = get_correct_lesson_type(subject[0])
        if lesson_type is not None:
            subject.pop(0)
        return lesson_type, ' '.join(subject)
