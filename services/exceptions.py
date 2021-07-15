class ExternalError(Exception):
    def __init__(self, message: str = 'Just error') -> None:
        print(f'Error: \n\t{message}')


class InternalError(Exception):
    def __init__(self, message: str = 'Just error') -> None:
        print(f'Error: \n\t{message}')
