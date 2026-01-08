from argparse import Namespace

from downloader import JWDownloader
from parsing import expand_ranges, parse_spec_to_ranges


def handler_lesson_subcmd(args: Namespace, jw_downloader: JWDownloader) -> None:
    lessons = list(
        expand_ranges(parse_spec_to_ranges(args.lesson), min_value=0, max_value=60)
    )
    jw_downloader.add_lessons_to_queue(lessons)
