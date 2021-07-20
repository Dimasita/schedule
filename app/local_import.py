import json
import os

from universities import *

UNIVERSITIES = {
    'spbstu': Spbstu,
    'unecon': Unecon,
    'etu': Etu,
    'bstu': Bstu,
    'itmo': Itmo
}

if __name__ == '__main__':
    university_name = os.getenv('university')

    university = UNIVERSITIES[university_name]()
    university.set_default_values()
    with open(fr'{os.getcwd()}\universities\{university_name}\data.json', 'w+', encoding='utf-8') as f:
        json.dump(university.get_values(), f, ensure_ascii=False)
