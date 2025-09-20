import colorama

from parsing import parse_spec_to_ranges, expand_ranges
from functions import parse_size_limit, parse_duration_limit
from jw_downloader import JWDownloader
from cli import parse_args


def main():
    parser, args = parse_args()
    if args.size_limit != -1:
        try:
            args.size_limit = parse_size_limit(args.size_limit)
        except ValueError:
            print(f"error: Incorrect format for size limit: {args.size_limit}")
            exit(1)
    if args.duration_limit != -1:
        try:
            args.duration_limit = parse_duration_limit(args.duration_limit)
        except ValueError:
            print(f"error: Incorrect format for duration limit: {args.duration_limit}")
            exit(1)

    jw_downloader = JWDownloader(quality=args.quality, max_size=args.size_limit or -1)

    if hasattr(args, "section"):
        try:
            if args.section == "all":
                for i in [";", "|", "."]:
                    content_type = "main"
                    splitted = args.section.split(i, 1)
                    if len(splitted) > 1:
                        content_type = splitted[1]
                sections = [(section, content_type) for section in range(1, 5)]
            else:
                sections = list(
                    expand_ranges(
                        parse_spec_to_ranges(args.section), min_value=1, max_value=4
                    )
                )
            jw_downloader.add_sections_to_queue(sections)
        except ValueError:
            parser.print_help()
            exit(1)
    elif hasattr(args, "lesson"):
        lessons = list(
            expand_ranges(parse_spec_to_ranges(args.lesson), min_value=0, max_value=60)
        )
        jw_downloader.add_lessons_to_queue(lessons)
    else:
        parser.print_help()
        exit(1)

    jw_downloader.exec()

    jw_downloader.start_download()


if __name__ == "__main__":
    main()
