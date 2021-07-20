from typing import Optional


def humanize_weekday(weekday) -> Optional[str]:
    if type(weekday) == str:
        weekday = weekday.lower()
    days = {
        1: 'пн', 2: 'вт', 3: 'ср', 4: 'чт', 5: 'пт', 6: 'сб', 7: 'вс',
        'mon': 'пн', 'tue': 'вт', 'wed': 'ср', 'thu': 'чт', 'fri': 'пт', 'sat': 'сб', 'sun': 'вс',
        'понедельник': 'пн', 'вторник': 'вт', 'среда': 'ср', 'четверг': 'чт', 'пятница': 'пт',
        'суббота': 'сб', 'воскресенье': 'вс'
    }
    if weekday not in days.keys():
        return None
    return days[weekday]


def get_correct_lesson_type(lesson_type: str) -> Optional[str]:
    lesson_type = lesson_type.lower()
    types = {
        'лек': 'Лек', 'лекции': 'Лек', 'лекция': 'Лек',
        'пр': 'Пр', 'прак': 'Пр', 'практические': 'Пр', 'практика': 'Пр', 'практическая': 'Пр',
        'лаб': 'Лаб', 'лабораторные': 'Лаб', 'лабораторная': 'Лаб'
    }
    if lesson_type not in types.keys():
        return None
    return types[lesson_type]
