import sys


class InvalidSection(BaseException):
    def __init__(self, section):
        print(
            f"Invalid section: {section}. Values must be: [1, 2, 3, 4]",
            file=sys.stderr,
        )


class InvalidLesson(BaseException):
    def __init__(self, lesson):
        print(
            f"Invalid lesson: {lesson}. Values must be in the range 0-60",
            file=sys.stderr,
        )


class InvalidContentType(BaseException):
    def __init__(self, content):
        print(
            f'Invalid content to download: {content}. Values must be in: ["all", "a", "main", "m", "extra", "e"]',
            file=sys.stderr,
        )
