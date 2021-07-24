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
from services.helper import humanize_weekday, get_correct_lesson_type
from services.requests import get_json, get_page, get_page_async, get_json_async
from universities.itmo.config import LINKS, MAX_PARALLEL_REQUESTS, FIRST_WEEK_MONDAY_DATE


class Itmo(University):
    current_week_number: int
    schedule_start_date: date
    schedule_end_date: date
    first_week: date

    def __init__(self):
        self._set_dates()

    @benchmark('set groups')
    def _set_groups(self) -> None:
        groups = self._parse_groups_page_to_list(get_page(LINKS['BASE'], 'GET'))
        for g in groups:
            self.groups[g['id']] = Group(g['id'], g['name'], level=g['level'])

    def _set_subjects(self) -> None:
        if len(self.schedule) == 0:
            self._set_schedule()
        subject_ids = set()
        for lesson in self.schedule:
            name = re.findall(r'(.+)\(', lesson['lesson'].find('td', class_='lesson').find('dd').text)[0]
            subject = Subject(name)
            if subject.id not in subject_ids:
                subject_ids.add(subject.id)
                self.subjects[subject.id] = subject

    def _set_teachers(self) -> None:
        if len(self.schedule) == 0:
            self._set_schedule()
        teachers_ids = set()
        for lesson in self.schedule:
            name = lesson['lesson'].find('b')
            if name is not None:
                name = name.text.strip()
                teacher = Teacher(sha256(name.encode('utf-8')).hexdigest(), name)
                if teacher.id not in teachers_ids:
                    teachers_ids.add(teacher.id)
                    self.teachers[teacher.id] = teacher

    @benchmark('set lessons')
    def _set_lessons(self) -> None:
        if len(self.schedule) == 0:
            self._set_schedule()
        for s in self.schedule:
            lesson = s['lesson']
            if len(lesson) == 0:
                continue
            groups = list()
            teachers = list()
            classrooms = list()
            tags = list()
            lesson_type = None

            full_subject = lesson.find('td', class_='lesson').find('dd').text
            subject_name = re.findall(r'(.+)\(', full_subject)[0]
            subject = self.subjects[sha256(subject_name.encode('utf-8')).hexdigest()]
            lesson_type_list = re.findall(r'\((\w)\)', full_subject)
            if len(lesson_type_list) > 0:
                lesson_type = get_correct_lesson_type(lesson_type_list[0])
            tag = re.findall(r':(\w)', full_subject)
            if len(tag) > 0:
                tags.append({'text': tag[0], 'link': None, 'type': 'gray'})

            lesson_format = lesson.find('td', class_='lesson-format').text.strip()
            tags.append({'text': lesson_format, 'link': None, 'type': 'gray'})

            t_name = lesson.find('b')
            if t_name is not None:
                t_name = t_name.text.strip()
                teachers.append(self.teachers[sha256(t_name.encode('utf-8')).hexdigest()])

            room = lesson.find('td', class_='room')
            classrooms.append({
                'name': room.find('dd').text.strip() if room.find('dd').text != '' else None,
                'building': room.find('span').text.strip() if room.find('span').text != '' else None
            })

            groups.append(self.groups[s['group_id']])
            times = lesson.find('td', class_='time').find('span').text
            start_time, end_time = self._get_times(times)
            self._add_lesson(Lesson(
                subject, groups, teachers, self._calculate_lesson_number(start_time),
                s['is_odd_week'], humanize_weekday(s['weekday']), start_time, end_time,
                lesson_type, classrooms, tags)
            )

    @benchmark('set schedule')
    def _set_schedule(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._set_events_to_get_schedule())

    async def _set_events_to_get_schedule(self) -> None:
        semaphore = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)
        await asyncio.wait([
            asyncio.create_task(self._extend_schedule(group, semaphore))
            for group in self.groups.values()
        ])

    async def _extend_schedule(self, group: Group, semaphore) -> None:
        async with semaphore:
            res = await self._get_schedule_for_single_group(group)
            self.schedule.extend(res)

    async def _get_schedule_for_single_group(self, group: Group) -> []:
        data = await get_page_async(
            rf'{LINKS["SINGLE"]}{group.name}/raspisanie_zanyatiy_{group.name}.htm',
            method='GET'
        )
        return self._parse_schedule_page_to_list(data, group.id)

    def _parse_schedule_page_to_list(self, soup: BeautifulSoup, group_id: int) -> [{}]:
        res = list()
        schedule = soup.find_all('div', class_='rasp_tabl_day')
        for s in schedule:
            try:
                weekday = re.findall(r'\d', s.table.attrs['id'])[0]
            except IndexError:
                weekday = None
            calendar_day = None
            lessons = s.find_all('tr')
            for lsn in lessons:
                if len(lsn) == 0:
                    continue

                if weekday is None:
                    res.append({'group_id': group_id, 'lesson': lsn, 'weekday': None, 'is_odd_week': None})
                    continue

                if len(re.findall('четная', lsn.find('td', class_='lesson').text)) == 1:
                    res.append({'group_id': group_id, 'lesson': lsn, 'weekday': weekday, 'is_odd_week': False})
                    continue
                if len(re.findall('нечетная', lsn.find('td', class_='lesson').text)) == 1:
                    res.append({'group_id': group_id, 'lesson': lsn, 'weekday': weekday, 'is_odd_week': True})
                    continue

                if calendar_day is None:
                    calendar_day = re.findall(r'(\d{1,2}.\d{1,2}.\d{2})', lsn.find('th', class_='day').text)
                if len(calendar_day) == 1:
                    day_to_date = datetime.strptime(calendar_day[0], '%d.%m.%y').date()
                    if self.schedule_start_date <= day_to_date < self.schedule_end_date:
                        res.append({
                            'group_id': group_id,
                            'lesson': lsn,
                            'weekday': weekday,
                            'is_odd_week': self._is_odd_week(day_to_date)
                        })
                        continue
                    else:
                        break

                weeks_numbers = lsn.find('td', class_='time')
                if weeks_numbers.find('div') is not None:
                    for week in weeks_numbers.find('div').text.split(','):
                        if int(week) == self.current_week_number:
                            res.append({
                                'group_id': group_id,
                                'lesson': lsn,
                                'weekday': weekday,
                                'is_odd_week': False if int(week) % 2 == 0 else True
                            })
                            continue
                        if int(week) == self.current_week_number + 1:
                            res.append({
                                'group_id': group_id,
                                'lesson': lsn,
                                'weekday': weekday,
                                'is_odd_week': True if int(week) % 2 == 0 else False
                            })
                else:
                    res.append({'group_id': group_id, 'lesson': lsn, 'weekday': weekday, 'is_odd_week': False})
                    res.append({'group_id': group_id, 'lesson': lsn, 'weekday': weekday, 'is_odd_week': True})
        return res

    def _set_dates(self) -> None:
        # :TODO удалить дельту недель в строке ниже потом!!!!!!
        today = date.today() - timedelta(weeks=16)

        self.first_week = datetime.strptime(FIRST_WEEK_MONDAY_DATE, '%d.%m.%Y').date()
        self.schedule_start_date = today - timedelta(days=today.weekday())
        self.schedule_end_date = self.schedule_start_date + timedelta(weeks=2)
        self.current_week_number = abs((self.first_week - self.schedule_start_date).days // 7) + 1

    def _is_odd_week(self, day: date) -> bool:
        weeks_delta = abs((day - self.first_week).days) // 7
        if weeks_delta % 2 == 0:
            return True
        return False

    @staticmethod
    def _parse_groups_page_to_list(soup: BeautifulSoup) -> [{}]:
        res = list()
        for i in range(1, 6):
            lst = soup.find('div', id=f'tab{i}')
            groups = lst.find_all('a')
            for g in groups:
                res.append({'id': sha256(g.text.encode('utf-8')).hexdigest(),
                            'link': g.href, 'name': g.text, 'level': i})
        return res

    @staticmethod
    def _calculate_lesson_number(start_time: time) -> int:
        table = {
            8: 1,
            10: 2,
            11: 3,
            13: 4,
            15: 5,
            17: 6,
            18: 7,
            20: 8
        }
        hours = start_time.hour
        if hours not in table.keys():
            return 0
        return table[hours]

    @staticmethod
    def _get_times(time_range: str) -> (time, time):
        times = time_range.split('-')
        return datetime.strptime(times[0], '%H:%M').time(), datetime.strptime(times[1], '%H:%M').time()
