from hashlib import sha256


class Subject:
    id: str
    name: str

    def __init__(self, name: str):
        self.name = name
        self.id = sha256(name.encode('utf-8')).hexdigest()
