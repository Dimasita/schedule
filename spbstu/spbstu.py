import re
import time
from datetime import date, datetime, timedelta
from hashlib import sha256
from bs4 import BeautifulSoup

from models.group import Group
from models.lesson import Lesson
from models.subject import Subject
from models.teacher import Teacher
from models.unversity_tamplate import UniversityTemplate
from services.decorators import benchmark
from services.exceptions import ExternalError
from services.helper import get_json, get_page
from spbstu.config import LINKS


class Spbstu(UniversityTemplate):

    @benchmark('set groups')
    def _set_groups(self) -> None:
        faculties = self._get_faculties()
        for f in faculties:
            for group in (list(map(
                lambda g: Group(g['id'], g['name'], f['name'], g['type'], g['level']),
                self._parse_groups_to_list(
                    self._get_groups_from_page(
                        get_page(LINKS['BASE'] + f['link'], 'GET')
                    )
                )
            ))):
                self.groups[group.id] = group

        # :TODO REMOVE THIS
        i = 0
        buff = dict()
        for key, value in self.groups.items():
            if i > 15:
                break
            i += 1
            buff[key] = value
        self.groups = buff
        # :TODO REMOVE THIS

    @benchmark('set teachers (includes set schedule)')
    def _set_teachers(self) -> None:
        if len(self.schedule) == 0:
            self._set_schedule()
        teachers_ids = set()
        for lesson in self.schedule:
            if lesson['lesson']['teachers'] is not None:
                for t in lesson['lesson']['teachers']:
                    if t['id'] not in teachers_ids:
                        teachers_ids.add(t['id'])
                        self.teachers[t['id']] = Teacher(
                            t['id'],
                            t['full_name'],
                            t['grade'],
                            t['oid']
                        )

    @benchmark('set subjects')
    def _set_subjects(self) -> None:
        if len(self.schedule) == 0:
            self._set_schedule()
        subject_ids = set()
        for lesson in self.schedule:
            if lesson['lesson']['subject'] is not None:
                subject = Subject(lesson['lesson']['subject'])
                if subject.id not in subject_ids:
                    subject_ids.add(subject.id)
                    self.subjects[subject.id] = subject

    @benchmark('set lessons')
    def _set_lessons(self) -> None:
        if len(self.schedule) == 0:
            self._set_schedule()
        for lesson in self.schedule:
            groups = list()
            teachers = list()
            classrooms = list()
            tags = list()
            if lesson['lesson']['groups'] is not None:
                for group in lesson['lesson']['groups']:

                    # :TODO REMOVE THIS
                    if group['id'] not in self.groups.keys():
                        self.groups[group['id']] = Group(group['id'], 'name', 'faculty', 'edu_type', 1)
                    # :TODO REMOVE THIS

                    groups.append(self.groups[group['id']])
            if lesson['lesson']['teachers'] is not None:
                for teacher in lesson['lesson']['teachers']:
                    teachers.append(self.teachers[teacher['id']])
            if lesson['lesson']['auditories'] is not None:
                for classroom in lesson['lesson']['auditories']:
                    classrooms.append({'name': classroom['name'], 'building': classroom['building']['name']})
            if lesson['lesson']['webinar_url'] is not None and lesson['lesson']['webinar_url'] != '':
                tags.append({'text': '', 'link': lesson['lesson']['webinar_url'], 'type': 'blue'})
            if lesson['lesson']['lms_url'] is not None and lesson['lesson']['lms_url'] != '':
                tags.append({'text': '', 'link': lesson['lesson']['lms_url'], 'type': 'blue'})
            if lesson['lesson']['typeObj'] is not None:
                lesson_type = lesson['lesson']['typeObj']['name']
            else:
                lesson_type = 'default'
            subject = self.subjects[sha256(lesson['lesson']['subject'].encode('utf-8')).hexdigest()]
            start_time = time.strptime(lesson['lesson']['time_start'], '%H:%M')
            end_time = time.strptime(lesson['lesson']['time_start'], '%H:%M')
            lesson_number = self._calculate_lesson_number(start_time)
            self.lessons.add(Lesson(
                subject, groups, teachers, lesson_number, lesson['is_odd_week'],
                self._humanize_weekday(lesson['weekday']), start_time, end_time,
                lesson_type, classrooms, tags)
            )

    @benchmark('set schedule')
    def _set_schedule(self) -> None:
        odd_week_start, even_week_start = self._get_mondays_date()
        for group in self.groups.values():
            self.schedule.extend(self._get_schedule_for_the_week(group.id, odd_week_start))
            self.schedule.extend(self._get_schedule_for_the_week(group.id, even_week_start))

    def _get_mondays_date(self) -> (datetime, datetime):
        week = self._get_current_week()

        # :TODO удалить дельту недель в строке ниже потом!!!!!!
        odd_week_start = datetime.strptime(week['date_start'], '%Y.%m.%d').date() - timedelta(weeks=16)
        even_week_start = odd_week_start + timedelta(days=7)
        if week['is_odd'] is False:
            return even_week_start, odd_week_start
        return odd_week_start, even_week_start

    def _get_current_week(self) -> {str: str}:
        keys = list(self.groups.keys())
        res = get_json(LINKS['GET_SCHEDULE_BY_GROUP'] + str(self.groups[keys[0]].id), 'GET')
        if 'week' not in res.keys():
            raise ExternalError('Invalid data')
        return {
            'date_start': res['week']['date_start'],
            'date_end': res['week']['date_end'],
            'is_odd': res['week']['is_odd']
        }

    @staticmethod
    def _get_schedule_for_the_week(group_id: int, first_week_day: date) -> [{}]:
        res = get_json(LINKS['GET_SCHEDULE_BY_GROUP'] + str(group_id), 'GET', date=first_week_day)
        return [{'date': x['date'],
                 'weekday': x['weekday'],
                 'lesson': y,
                 'group_id': group_id,
                 'is_odd_week': res['week']['is_odd']}
                for x in res['days'] for y in x['lessons']]

    @staticmethod
    def _get_faculties() -> [str]:
        soup = get_page(LINKS['BASE'])
        faculties = soup.find_all('a', class_='faculty-list__link')
        return [{'link': f.get('href'), 'name': f.text} for f in faculties]

    @staticmethod
    def _get_groups_from_page(soup: BeautifulSoup) -> str:
        res = soup.find_all('script')
        for r in res:
            if r.string is not None and len(r.attrs) == 0:
                return r.string

    @staticmethod
    def _parse_groups_to_list(groups: str) -> [{str, str}]:
        pattern = re.compile(r'"id":(?P<id>\d+),"name":"(?P<name>\w+/\w+)",'
                             r'"level":(?P<level>\d+),"type":"(?P<type>\w+)"')
        return [m.groupdict() for m in pattern.finditer(groups)]

    @staticmethod
    def _calculate_lesson_number(start_time: time) -> int:
        # :TODO (idk how to calculate this)
        return 0

    @staticmethod
    def _humanize_weekday(weekday: int) -> str:
        days = {
            1: 'пн',
            2: 'вт',
            3: 'ср',
            4: 'чт',
            5: 'пт',
            6: 'сб',
            7: 'вс'
        }
        return days[weekday]
