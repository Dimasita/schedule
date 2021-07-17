import json
import time

from spbstu.spbstu import Spbstu

UNIVERSITIES = {
    'spbstu': Spbstu
}

if __name__ == '__main__':
    university = UNIVERSITIES['spbstu']()
    university.set_default_values()
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(university.get_values(), f, ensure_ascii=False)
