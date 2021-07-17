import json
import time

from spbstu.spbstu import Spbstu

UNIVERSITIES = {
    'spbstu': Spbstu
}

if __name__ == '__main__':
    university = UNIVERSITIES['spbstu']()
    start = time.time()
    university.set_default_values()
    print(time.time() - start)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(university.get_values(), f, ensure_ascii=False)
