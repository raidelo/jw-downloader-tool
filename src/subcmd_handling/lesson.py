from argparse import Namespace

from cli import DesiredProps
from downloader import JWDownloader
from parsing import DEFAULT_SUFFIX, expand_ranges, parse_spec_to_ranges
from subcmd_handling import AUTO_RESOLVE
from subcmd_handling.downloading import download_lesson
from types_ import JWSectionMediaSummary, LessonID, SectionID

FIRST_LESSON = 0
LAST_LESSON = 60
SECTIONS_LESSONS = {
    1: (0, 12),
    2: (13, 33),
    3: (34, 47),
    4: (48, 60),
}


def get_section_of_lesson(lesson_n: LessonID) -> SectionID:
    for section, lessons_range in SECTIONS_LESSONS.items():
        if lesson_n > lessons_range[0] and lesson_n < lessons_range[1]:
            return section
    raise ValueError(
        f"`lesson_n` must be in the range {FIRST_LESSON}-{LAST_LESSON}: {lesson_n}"
    )


def handler_lesson_subcmd(args: Namespace, desired_props: DesiredProps) -> None:
    ranges = parse_spec_to_ranges(
        spec=args.lesson,
        min_value=FIRST_LESSON,
        max_value=LAST_LESSON,
        default_suffix=DEFAULT_SUFFIX,
    )

    sections: dict[SectionID, JWSectionMediaSummary] = {}

    for lesson_to_download in expand_ranges(ranges=ranges):
        section = get_section_of_lesson(lesson_to_download.n)

        if sections.get(section) is None:
            section_summary = JWDownloader.get_sect_data_parsed(
                section=section, resolve=AUTO_RESOLVE
            )
            sections[section] = section_summary
        else:
            section_summary = sections[section]

        for lesson_media in section_summary.lessons:
            if lesson_to_download.n == lesson_media.number:
                download_lesson(
                    lesson=lesson_media,
                    subsection=lesson_to_download.suffix,
                    desired_props=desired_props,
                )
