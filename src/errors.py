class InvalidSection(BaseException):
    def __init__(self, section):
        super().__init__(f"Invalid section: {section}. Values must be: [1, 2, 3, 4]")


class InvalidLesson(BaseException):
    def __init__(self, lesson):
        super().__init__(f"Invalid lesson: {lesson}. Values must be in the range 0-60")


class InvalidSubSection(BaseException):
    def __init__(self, content):
        super().__init__(
            f'Invalid sub-section to download: {content}. Values must be in: ["all", "a", "main", "m", "extra", "e"]'
        )
