from argparse import Namespace

from cli import DesiredProps
from downloader import JWDownloader
from parsing import DEFAULT_SUFFIX, expand_ranges, parse_spec_to_ranges
from subcmd_handling import AUTO_RESOLVE
from subcmd_handling.downloading import download_lesson

FIRST_SECTION = 1
LAST_SECTION = 4


def handler_section_subcmd(args: Namespace, desired_props: DesiredProps) -> None:
    ranges = parse_spec_to_ranges(
        spec=args.section,
        min_value=FIRST_SECTION,
        max_value=LAST_SECTION,
        default_suffix=DEFAULT_SUFFIX,
    )

    for section in expand_ranges(ranges=ranges):
        section_summary = JWDownloader.get_sect_data_parsed(
            section=section.n, resolve=AUTO_RESOLVE
        )

        for lesson in section_summary.lessons:
            download_lesson(
                lesson=lesson,
                subsection=section.suffix,
                desired_props=desired_props,
            )
