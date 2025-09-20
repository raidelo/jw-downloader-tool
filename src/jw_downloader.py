from collections import OrderedDict
from pathlib import Path

from bs4 import BeautifulSoup
import requests

from constants import BASE_URL, LESSON_NUMBER_RE, SECTIONS
from errors import InvalidContentType, InvalidSection, InvalidLesson
from functions import rm_wrong_chars


class JWDownloader:
    CONTENT = {
        "all": "a",
        "main": "m",
        "extra": "e",
        "a": "a",
        "m": "m",
        "e": "e",
    }

    def __init__(
        self, quality: str | int = 720, max_size: int = -1, max_duration: int = -1
    ):
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

        if not isinstance(max_size, int):
            raise TypeError("Argument `max_file_size` must be an `int`")
        self.max_size = max_size
        self.max_duration = max_duration

        self.queue = OrderedDict()
        for i in range(1, 5):
            self.queue[i] = []

    def add_sections_to_queue(self, sections: list[int]):
        for section, content_type in sections:
            if section < 1 or section > 4:
                raise InvalidSection(section)
            if content_type not in self.CONTENT.keys():
                raise InvalidContentType(content_type)
            first_lesson, last_lesson = SECTIONS[section]
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
            for section, range_ in SECTIONS.items():
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
                            p = Path(url.split("?")[0])
                            filename = rm_wrong_chars(p.name.replace(p.stem, title))

                            if not best_quality_variant:
                                print("\nVídeo no encontrado para:")
                                print(f"  Título: {filename}")
                                print(f"  Url: {url}")
                                continue
                            if (
                                self.max_size != -1
                                and best_quality_variant["filesize"] > self.max_size
                            ):
                                print(
                                    "\nIgnorando vídeo. Su tamaño excede el máximo permitido."
                                )
                                continue
                            if (
                                self.max_duration != -1
                                and best_quality_variant["duration"] > self.max_duration
                            ):
                                print(
                                    "\nIgnorando vídeo. Su duración excede el máximo permitido."
                                )
                                continue

                            def descargar_archivo(url, path):
                                print(f"\nDescargando archivo: {path.name}")
                                print(f"Ruta: {path}")
                                print(f"Url: {url}")
                                print(f"Qual: {best_quality_variant['label']}")
                                print("Archivo descargado con éxito!\n")

                            if key == "main":
                                descargar_archivo(url, lesson_path.joinpath(filename))
                            else:
                                extra_lesson_path = lesson_path.joinpath(
                                    "Descubra algo más"
                                )
                                extra_lesson_path.mkdir(parents=True, exist_ok=True)
                                descargar_archivo(
                                    url,
                                    extra_lesson_path.joinpath(filename),
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
