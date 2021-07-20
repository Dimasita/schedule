import json

from unversities import *

UNIVERSITIES = {
    'spbstu': Spbstu,
    'unecon': Unecon,
    'etu': Etu,
    'bstu': Bstu,
    'itmo': Itmo
}

if __name__ == '__main__':
    university = UNIVERSITIES['spbstu']()
    university.set_default_values()
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(university.get_values(), f, ensure_ascii=False)
