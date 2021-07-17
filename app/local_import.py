import json

from bstu.bstu import Bstu
from etu.etu import Etu
from spbstu.spbstu import Spbstu

UNIVERSITIES = {
    'spbstu': Spbstu,
    'etu': Etu,
    'bstu': Bstu
}

if __name__ == '__main__':
    university = UNIVERSITIES['etu']()
    university.set_default_values()
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(university.get_values(), f, ensure_ascii=False)
