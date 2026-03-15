from argparse import ArgumentParser


def argument_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--quality", default="720", dest="quality")
    parser.add_argument("-l", "--size-limit", default=-1, dest="size_limit")
    parser.add_argument("-d", "--duration-limit", default=-1, dest="duration_limit")

    subcmd = parser.add_subparsers(required=True)
    subcommand_section = subcmd.add_parser("section")
    subcommand_section.add_argument("section")

    subcommand_lesson = subcmd.add_parser("lesson")
    subcommand_lesson.add_argument("lesson")

    return parser
