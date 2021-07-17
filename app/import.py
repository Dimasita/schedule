import json
import sys
from json import JSONDecodeError

from spbstu.spbstu import Spbstu

UNIVERSITIES = {
    'spbstu': Spbstu
}

if __name__ == '__main__':
    if len(sys.argv) == 1:
        exit('Select university!')
    if len(sys.argv) > 2:
        exit('Too many arguments!')
    if sys.argv[1] not in UNIVERSITIES.keys():
        exit('Wrong university name!')

    university = UNIVERSITIES[sys.argv[1]]()

    if not sys.stdin.isatty():
        try:
            data = json.load(sys.stdin)
        except JSONDecodeError:
            university.set_default_values()
        else:
            university.set_values_from_file(data)
    else:
        university.set_default_values()

    json.dump(university.get_values(), sys.stdout)
