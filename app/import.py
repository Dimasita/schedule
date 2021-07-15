import json
import sys

from spbstu.spbstu import Spbstu

UNIVERSITIES = {
    'spbstu': Spbstu
}

if __name__ == '__main__':
    if len(sys.argv) == 1:
        exit('Select university!')
    if len(sys.argv) > 2:
        exit('Too many arguments!')
    university = UNIVERSITIES[sys.argv[1]]()

    if not sys.stdin.isatty():
        university.set_values_from_file(json.load(sys.stdin))
    else:
        university.set_default_values()

    json.dump(university.get_values(), sys.stdout)
