from argparse import Namespace

from constants import AMOUNT_OF_SECTIONS, DEFAULT_MODE
from downloader import JWDownloader
from parsing import expand_ranges, parse_spec_to_ranges


def handler_section_subcmd(args: Namespace, jw_downloader: JWDownloader) -> None:
    match = SECTION_ALL_RE.match(args.section)
    if match:
        sub_section = match.group(2) or DEFAULT_MODE
        sections = [
            (section, sub_section) for section in range(1, AMOUNT_OF_SECTIONS + 1)
        ]
    else:
        sections = list(
            expand_ranges(parse_spec_to_ranges(args.section), min_value=1, max_value=4)
        )
    jw_downloader.add_sections_to_queue(sections)
