import asyncio
import re
from datetime import date, datetime, timedelta, time
from hashlib import sha256
from bs4 import BeautifulSoup

from models.group import Group
from models.lesson import Lesson
from models.subject import Subject
from models.teacher import Teacher
from universities.university import University
from services.decorators import benchmark
from services.exceptions import ExternalError
from services.helper import humanize_weekday, get_correct_lesson_type
from services.requests import get_json, get_page, get_page_async, get_json_async
from universities.spbstu.config import LINKS, MAX_PARALLEL_REQUESTS


class Spbstu(University):
    @benchmark('set groups')
    def _set_groups(self) -> None:
        faculties = self._get_faculties()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._set_events_to_get_groups(faculties))

    async def _set_events_to_get_groups(self, faculties: []) -> None:
        semaphore = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)
        await asyncio.wait([
            asyncio.create_task(self._extend_groups(faculty, semaphore))
            for faculty in faculties
        ])

    async def _extend_groups(self, faculty, semaphore) -> None:
        async with semaphore:
            page = await self._get_groups_from_page(faculty)
            for group in (list(map(
                    lambda g: Group(g['id'], g['name'], faculty['name'], g['type'], g['level']),
                    self._parse_groups_to_list(page)
            ))):
                self.groups[group.id] = group

    @staticmethod
    async def _get_groups_from_page(faculty) -> BeautifulSoup:
        soup = await get_page_async(LINKS['BASE'] + faculty['link'], 'GET')
        return soup

    @staticmethod
    def _parse_groups_page_to_string(soup: BeautifulSoup) -> str:
        res = soup.find_all('script')
        for r in res:
            if r.string is not None and len(r.attrs) == 0:
                return r.string

    def _parse_groups_to_list(self, page: BeautifulSoup) -> [{str, str}]:
        groups = self._parse_groups_page_to_string(page)
        pattern = re.compile(r'"id":(?P<id>\d+),"name":"(?P<name>\w+/\w+)",'
                             r'"level":(?P<level>\d+),"type":"(?P<type>\w+)"')
        return [m.groupdict() for m in pattern.finditer(groups)]

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
                    groups.append(self.groups[str(group['id'])])
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
                lesson_type = get_correct_lesson_type(lesson['lesson']['typeObj']['name'])
            else:
                lesson_type = None
            subject = self.subjects[sha256(lesson['lesson']['subject'].encode('utf-8')).hexdigest()]
            start_time = datetime.strptime(lesson['lesson']['time_start'], '%H:%M').time()
            end_time = datetime.strptime(lesson['lesson']['time_start'], '%H:%M').time()
            lesson_number = self._calculate_lesson_number(start_time, end_time)
            self._add_lesson(Lesson(
                subject, groups, teachers, lesson_number, lesson['is_odd_week'],
                humanize_weekday(lesson['weekday']), start_time, end_time,
                lesson_type, classrooms, tags)
            )

    @benchmark('set schedule')
    def _set_schedule(self) -> None:
        odd_week_start, even_week_start = self._get_mondays_date()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._set_events_to_get_schedule(odd_week_start, even_week_start))

    async def _set_events_to_get_schedule(self, odd_week_start: date, even_week_start: date) -> None:
        semaphore = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)
        await asyncio.wait([
            asyncio.create_task(self._extend_schedule(group, odd_week_start, even_week_start, semaphore))
            for group in self.groups.values()
        ])

    async def _extend_schedule(self, group: Group, odd_week_start: date, even_week_start: date, semaphore):
        async with semaphore:
            odd = await self._get_schedule_for_the_week(group.id, odd_week_start)
            even = await self._get_schedule_for_the_week(group.id, even_week_start)
            self.schedule.extend(odd)
            self.schedule.extend(even)

    @staticmethod
    async def _get_schedule_for_the_week(group_id: str, first_week_day: date) -> [{}]:
        res = await get_json_async(
            LINKS['GET_SCHEDULE_BY_GROUP'] + str(group_id),
            method='GET',
            date=first_week_day.strftime('%Y-%m-%d')
        )
        return [{'date': x['date'],
                 'weekday': x['weekday'],
                 'lesson': y,
                 'group_id': group_id,
                 'is_odd_week': res['week']['is_odd']}
                for x in res['days'] for y in x['lessons']]

    def _get_mondays_date(self) -> (date, date):
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
    def _get_faculties() -> [str]:
        soup = get_page(LINKS['BASE'])
        faculties = soup.find_all('a', class_='faculty-list__link')
        return [{'link': f.get('href'), 'name': f.text} for f in faculties]

    @staticmethod
    def _calculate_lesson_number(start_time: time, end_time: time) -> int:
        start = timedelta(hours=start_time.hour, minutes=start_time.minute)
        end = timedelta(hours=end_time.hour + 1, minutes=end_time.minute + 30)
        delta = end - start
        if delta.total_seconds() != 5400 and delta.total_seconds() != 6000:
            return 0
        table = {
            8: 1,
            10: 2,
            12: 3,
            14: 4,
            16: 5,
            18: 6,
            20: 7
        }
        hours = start_time.hour
        if hours not in table.keys():
            return 0
        return table[hours]
