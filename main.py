from argparse import ArgumentParser
from collections import OrderedDict
from pathlib import Path
import re

from bs4 import BeautifulSoup
import colorama
import requests

from download import descargar_archivo
from errors import InvalidContentType, InvalidSection, InvalidLesson
from parsing import parse_spec_to_ranges, expand_ranges

BASE_URL = "https://www.jw.org/es/biblioteca/libros/disfrute-vida-para-siempre/seccion-%s/multimedia/"
LESSON_NUMBER_RE = re.compile(r"^(\d{1,2})\s+.*")
SIZE_LIMIT_RE = re.compile(r"^(\d{1,}(\.\d{1,})?)(b|k|m|g|B|K|M|G)?")


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--quality", default="720", dest="quality")
    parser.add_argument("-l", "--size-limit", default=-1, dest="size_limit")

    subcmd = parser.add_subparsers(required=True)
    subcommand_section = subcmd.add_parser("section")
    subcommand_section.add_argument("section")

    subcommand_lesson = subcmd.add_parser("lesson")
    subcommand_lesson.add_argument("lesson")

    return parser, parser.parse_args()


def rm_wrong_chars(s: str) -> str:
    r"""Remves following chars from the string:
    < (less than)
    > (greater than)
    : (colon - sometimes works, but is actually NTFS Alternate Data Streams)
    " (double quote)
    / (forward slash)
    \ (backslash)
    | (vertical bar or pipe)
    ? (question mark)
    * (asterisk)
    """
    chars = r'<>:"/\|?*'
    return "".join([c for c in s if c not in chars])


class JWDownloader:
    SECTIONS = (
        (0, 12),
        (13, 33),
        (34, 47),
        (48, 60),
    )
    CONTENT = {
        "all": "a",
        "main": "m",
        "extra": "e",
        "a": "a",
        "m": "m",
        "e": "e",
    }

    def __init__(self, quality: str | int = 720, max_file_size: int = -1):
        if isinstance(quality, int):
            self.quality = quality
        elif isinstance(quality, str):
            try:
                self.quality = int(quality.strip("pP "))
            except ValueError:
                raise ValueError(
                    "Argument `quality` must be the number alone or end in `p` or `P`\nExamples: 720p, 360P, 240"
                )
        else:
            raise TypeError("Argument `quality` must be either an `int` or a `str`")

        if not isinstance(max_file_size, int):
            raise TypeError("Argument `max_file_size` must be an `int`")
        self.max_file_size = max_file_size

        self.queue = OrderedDict()
        for i in range(1, 5):
            self.queue[i] = []

    def add_sections_to_queue(self, sections: list[int]):
        for section, content_type in sections:
            if section < 1 or section > 4:
                raise InvalidSection(section)
            if content_type not in self.CONTENT.keys():
                raise InvalidContentType(content_type)
            first_lesson, last_lesson = self.SECTIONS[section - 1]
            self.queue[section] = [
                (lesson, self.CONTENT[content_type])
                for lesson in range(first_lesson, last_lesson + 1)
            ]

    def add_lessons_to_queue(self, lessons: list[int]):
        for lesson, content_type in lessons:
            if lesson < 0 or lesson > 60:
                raise InvalidLesson(lesson)
            if content_type not in self.CONTENT.keys():
                raise InvalidContentType(content_type)
            for section, range_ in enumerate(self.SECTIONS, 1):
                if lesson >= range_[0] and lesson <= range_[1]:
                    self.queue[section].append((lesson, content_type))

    def exec(self):
        for section in self.queue:
            self.queue[section].sort()

        for section in self.queue:
            if self.queue[section]:
                section_info = self.__get_info_of_section(section)
                new_section_queue = []

                for lesson, content_type in self.queue[section]:
                    lesson_info = section_info[lesson]

                    if content_type in ["all", "a"]:
                        pass
                    elif content_type in ["main", "m"]:
                        lesson_info.pop("extra")
                    elif content_type in ["extra", "e"]:
                        lesson_info.pop("main")

                    new_section_queue.append(lesson_info)

                self.queue[section] = new_section_queue

    def start_download(self):
        root_path = Path(__file__).with_name("Disfrute de la vida para siempre!")
        root_path.mkdir(parents=True, exist_ok=True)

        print("Comenzando descarga ...")

        for section in self.queue:
            if not self.queue[section]:
                continue

            print(f"\nComenzando descarga de la sección {section} ...\n")

            section_path = root_path.joinpath(f"Sección {section}")
            section_path.mkdir(parents=True, exist_ok=True)

            for lesson in self.queue[section]:
                lesson_title = lesson["title"]

                print(
                    f"\nComenzando descarga del contenido de la lección {self.__get_lesson_number_from_title(lesson_title)} ...\n"
                )

                lesson_path = section_path.joinpath(rm_wrong_chars(lesson_title))
                lesson_path.mkdir(parents=True, exist_ok=True)

                for key in ["main", "extra"]:
                    try:
                        for api_link in lesson[key]:
                            properties = self.get_video_properties_from_api(api_link)
                            best_quality_variant = self.__get_best_quality_from(
                                properties
                            )
                            title = best_quality_variant["title"]
                            url = best_quality_variant["file"]["url"]
                            filesize = best_quality_variant["filesize"]

                            if not best_quality_variant:
                                print("\nVídeo no encontrado para:")
                                print(f"  Título: {title}")
                                print(f"  Url: {url}")
                                continue
                            if (
                                self.max_file_size != -1
                                and filesize > self.max_file_size
                            ):
                                print(
                                    "\nIgnorando vídeo. Su tamaño excede el máximo permitido."
                                )
                                continue

                            def descargar_archivo(url, path):
                                print(f"\nDescargando archivo: {path.name}")
                                print(f"Ruta: {path}")
                                print(f"Url: {url}")
                                print(f"Qual: {best_quality_variant['label']}")
                                print(f"Filesize: {filesize}")
                                print("Archivo descargado con éxito!\n")

                            if key == "main":
                                descargar_archivo(
                                    url, lesson_path.joinpath(rm_wrong_chars(title))
                                )
                            else:
                                extra_lesson_path = lesson_path.joinpath(
                                    "Descubra algo más"
                                )
                                extra_lesson_path.mkdir(parents=True, exist_ok=True)
                                descargar_archivo(
                                    url,
                                    extra_lesson_path.joinpath(rm_wrong_chars(title)),
                                )

                    except KeyError:
                        continue

                print(f"\n\u2705 Lección {lesson_title} finalizada ...\n")

            print(f"\n\u2705 Sección {section} descargada con éxito.\n")

        print("\n\u2705 Descarga completada!")

    def __get_best_quality_from(self, properties: dict) -> dict:
        best_match, index_of_best_match = 0, None
        for variant_pos, variant in enumerate(properties):
            curr_quality = int(variant["label"].strip("pP "))
            if curr_quality == self.quality:
                return properties[variant_pos]
            elif curr_quality > best_match and curr_quality < self.quality:
                best_match, index_of_best_match = curr_quality, variant_pos
        if index_of_best_match:
            return properties[index_of_best_match]

    @classmethod
    def __get_info_of_section(cls, section: int) -> OrderedDict:
        r = requests.get(BASE_URL % section)
        soup = BeautifulSoup(r.content, "html.parser")

        main_content = soup.find("main", {"id": "content"})
        nav_bar = main_content.find("div", {"id": "tt3"})
        siblings = nav_bar.find_next_siblings()

        summary, current_lesson_title = OrderedDict(), ""
        in_lessons_main, in_lessons_extra = False, False

        for sibling in siblings:
            if sibling.name == "h2":
                in_lessons_main, in_lessons_extra = True, False
                current_lesson_title = sibling.text.strip()
                current_lesson_number = cls.__get_lesson_number_from_title(
                    current_lesson_title
                )
                summary[current_lesson_number] = {
                    "title": current_lesson_title,
                    "main": [],
                    "extra": [],
                }
                continue

            if in_lessons_main:
                if cls.__is_extra(sibling):
                    in_lessons_main, in_lessons_extra = False, True
                    continue

                video_link = cls.__get_video_link(sibling)
                if video_link:
                    summary[current_lesson_number]["main"].append(video_link)

            if in_lessons_extra:
                video_link = cls.__get_video_link(sibling)
                if video_link:
                    summary[current_lesson_number]["extra"].append(video_link)

        return summary

    @staticmethod
    def __get_lesson_number_from_title(title: str) -> int:
        match = LESSON_NUMBER_RE.match(title)
        if match:
            return int(match.group(1))
        else:
            return 0

    @staticmethod
    def get_video_properties_from_api(api_link: str) -> dict:
        return requests.get(api_link).json()["files"]["S"]["MP4"]

    @staticmethod
    def __get_video_link(tag):
        a = tag.find("a")
        if a is not None and a.text == "Descargar este video":
            return a.attrs["href"]

    @staticmethod
    def __is_extra(tag) -> bool:
        try:
            tag.attrs["class"].index("du-color--coolGray-500")
            contains_class = True
        except ValueError:
            contains_class = False
        return tag.name == "h3" and contains_class


def parse_size_limit(size: str) -> int:
    match = SIZE_LIMIT_RE.match(size)
    multipliers = {
        "b": 10**0,
        "k": 10**3,
        "m": 10**6,
        "g": 10**9,
        "B": 10**0,
        "K": 10**3,
        "M": 10**6,
        "G": 10**9,
    }
    if match:
        ammount = match.group(1)
        multiplier = match.group(3)
        return int(float(ammount) * (multipliers[multiplier] if multiplier else 1))
    else:
        raise ValueError("Incorrect format for size limit")


def main():
    parser, args = parse_args()
    if args.size_limit != -1:
        try:
            args.size_limit = parse_size_limit(args.size_limit)
        except ValueError:
            print(f"error: Incorrect format for size limit: {args.size_limit}")
            exit(1)

    jw_downloader = JWDownloader(
        quality=args.quality, max_file_size=args.size_limit or -1
    )

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
