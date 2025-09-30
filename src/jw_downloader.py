from collections import OrderedDict
from pathlib import Path

from bs4 import BeautifulSoup
from requests import JSONDecodeError
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from constants import SECTION_MULTIMEDIA_URL, LESSON_NUMBER_RE, SECTIONS, SUB_SECTIONS
from console import Console
from download import download_archive
from errors import InvalidSubSection, InvalidSection, InvalidLesson
from functions import mkdirs, rm_wrong_chars
from http_client_session import session

SectionID = int
LessonID = int
SubSection = str

LessonInfo = dict[str, str | list[str]]


class JWDownloader:

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

        if not isinstance(max_duration, int):
            raise TypeError("Argument `max_duration` must be an `int`")

        self.max_size = max_size
        self.max_duration = max_duration

        self.queue: OrderedDict[SectionID, list[tuple[LessonID, SubSection]]] = (
            OrderedDict()
        )
        for i in range(1, 5):
            self.queue[i] = []

        self.to_download_queue: OrderedDict[
            SectionID, OrderedDict[LessonID, LessonInfo]
        ] = OrderedDict()

        self.completed = []

    def add_sections_to_queue(self, sections: list[tuple[SectionID, SubSection]]):
        for section, sub_section in sections:
            if section < 1 or section > 4:
                raise InvalidSection(section)
            if sub_section not in SUB_SECTIONS:
                raise InvalidSubSection(sub_section)
            first_lesson, last_lesson = SECTIONS[section]
            self.queue[section] = [
                (lesson, SUB_SECTIONS[sub_section])
                for lesson in range(first_lesson, last_lesson + 1)
            ]

    def add_lessons_to_queue(self, lessons: list[tuple[LessonID, SubSection]]):
        for lesson, sub_section in lessons:
            if lesson < 0 or lesson > 60:
                raise InvalidLesson(lesson)
            if sub_section not in SUB_SECTIONS:
                raise InvalidSubSection(sub_section)
            for section, (first_lesson, last_lesson) in SECTIONS.items():
                if lesson >= first_lesson and lesson <= last_lesson:
                    self.queue[section].append((lesson, sub_section))
                    break

    def exec(self, console: Console):
        with Progress(console=console) as progress:
            for section, lessons in self.queue.items():
                if not lessons:
                    continue

                self.to_download_queue.update([(section, OrderedDict())])

                task = progress.add_task(
                    f"[bold yellow]Getting information for Section {section}",
                    total=None,
                )

                lessons.sort()

                section_info = self.__get_info_of_section(section)

                for lesson, sub_section in lessons:
                    lesson_info = section_info[lesson]

                    if sub_section in ["all", "a"]:
                        pass
                    elif sub_section in ["main", "m"]:
                        lesson_info.pop("extra")
                    elif sub_section in ["extra", "e"]:
                        lesson_info.pop("main")

                    self.to_download_queue[section].update([(lesson, lesson_info)])

                progress.remove_task(task)

    def start_download(self, console: Console) -> list[str]:
        self.completed = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[green]{task.completed}/{task.total}"),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=console,
            transient=True,
        ) as progress:
            root_path = mkdirs(Path().joinpath("Disfrute de la vida para siempre!"))

            for section, lessons in self.to_download_queue.items():
                if not lessons:
                    continue

                console.print(f"\n[bold yellow]\u25b6 Sección {section}[/bold yellow]")

                section_path = mkdirs(root_path.joinpath(f"Sección {section}"))

                for _lesson, lesson_info in lessons.items():
                    lesson_title = lesson_info["title"]

                    console.print(f"  [cyan]Lección {lesson_title}[/cyan]")

                    lesson_path = mkdirs(
                        section_path.joinpath(rm_wrong_chars(lesson_title))
                    )

                    videos: list[tuple[str, str]] = []

                    subsection_main = lesson_info.get("main")
                    if subsection_main:
                        videos += [("main", api_link) for api_link in subsection_main]

                    subsection_extra = lesson_info.get("extra")
                    if subsection_extra:
                        videos += [("extra", api_link) for api_link in subsection_extra]

                    for subsection, api_link in videos:
                        try:
                            properties = self.get_video_properties_from_api(api_link)
                        except JSONDecodeError:
                            console.print(
                                "error: The remote server responded with an invalid response"
                            )
                            continue
                        try:
                            properties = properties["files"]["S"]["MP4"]
                        except KeyError:
                            console.print("error: Couldn't find the link for the video")
                            continue

                        best_quality = self.get_best_quality_from(
                            properties, self.quality
                        )
                        if not best_quality:
                            console.print(
                                "Couldn't find the desired quality for the video"
                            )
                            continue

                        size = best_quality["filesize"]
                        video_title = best_quality["title"]
                        video_url = best_quality["file"]["url"]

                        if self.max_size != -1 and size > self.max_size:
                            console.print(
                                f'[bold gray]Ignorando vídeo: "{video_title}" Su tamaño excede el máximo permitido.[/]'
                            )
                            continue
                        if (
                            self.max_duration != -1
                            and best_quality["duration"] > self.max_duration
                        ):
                            console.print(
                                f'[bold gray]Ignorando vídeo: "{video_title}" Su duración excede el máximo permitido.[/]'
                            )
                            continue

                        filename = rm_wrong_chars(
                            video_title
                            + "".join(Path(video_url.split("?")[0]).suffixes)
                        )

                        task = progress.add_task(
                            f"Descargando: {video_title}", total=size
                        )

                        written = 0

                        if subsection == "main":
                            file_path = lesson_path.joinpath(filename)
                        else:  # subsection == "extra"
                            file_path = mkdirs(
                                lesson_path.joinpath("Descubra algo más")
                            ).joinpath(filename)

                        for bytes_written in download_archive(
                            video_url, size, file_path
                        ):
                            progress.update(task, advance=bytes_written)
                            written += bytes_written
                            if written == size:
                                break

                        progress.remove_task(task)
                        self.completed.append(video_title)
                        console.print(
                            f"    [bold][green]✔ {video_title}[/bold] descargado[/green]"
                        )

    @staticmethod
    def get_best_quality_from(properties: dict, quality: int) -> dict | None:
        best_match, index_of_best_match = 0, None
        for variant_pos, variant in enumerate(properties):
            curr_quality = int(variant["label"].strip("pP "))
            if curr_quality == quality:
                return properties[variant_pos]
            elif curr_quality > best_match and curr_quality < quality:
                best_match, index_of_best_match = curr_quality, variant_pos
        if index_of_best_match:
            return properties[index_of_best_match]
        return None

    @classmethod
    def __get_info_of_section(
        cls, section: SectionID
    ) -> OrderedDict[LessonID, LessonInfo]:
        r = session.get(SECTION_MULTIMEDIA_URL % section)
        soup = BeautifulSoup(r.content, "html.parser")

        main_content = soup.find("main", {"id": "content"})
        nav_bar = main_content.find("div", {"id": "tt3"})
        siblings = nav_bar.find_next_siblings()

        section_summary: OrderedDict[LessonID, LessonInfo] = OrderedDict()
        current_lesson_title = ""
        in_subsection_main, in_subsection_extra = False, False

        for sibling in siblings:
            if sibling.name == "h2":
                in_subsection_main, in_subsection_extra = True, False
                current_lesson_title = sibling.text.strip()
                current_lesson_number = cls.__get_lesson_number_from_title(
                    current_lesson_title
                )
                section_summary[current_lesson_number] = {
                    "title": current_lesson_title,
                    "main": [],
                    "extra": [],
                }
                continue

            if in_subsection_main:
                if cls.__is_subsection_extra_header(sibling):
                    in_subsection_main, in_subsection_extra = False, True
                    continue

                video_link = cls.__get_video_link(sibling)
                if video_link:
                    section_summary[current_lesson_number]["main"].append(video_link)

            if in_subsection_extra:
                video_link = cls.__get_video_link(sibling)
                if video_link:
                    section_summary[current_lesson_number]["extra"].append(video_link)

        return section_summary

    @staticmethod
    def __get_lesson_number_from_title(title: str) -> LessonID:
        match = LESSON_NUMBER_RE.match(title)
        if match:
            return int(match.group(1))
        else:
            return 0

    @staticmethod
    def get_video_properties_from_api(api_link: str) -> dict:
        return session.get(api_link).json()

    @staticmethod
    def __get_video_link(tag) -> str | None:
        a = tag.find("a")
        if a is not None and a.text == "Descargar este video":
            return a.attrs["href"]

    @staticmethod
    def __is_subsection_extra_header(tag) -> bool:
        try:
            tag.attrs["class"].index("du-color--coolGray-500")
            contains_class = True
        except ValueError:
            contains_class = False
        return tag.name == "h3" and contains_class

    def summary_table(self) -> Table:
        table = Table(title="Resumen de descargas")
        table.add_column("Sección", justify="center", style="cyan", no_wrap=True)
        table.add_column("Lecciones", style="magenta")

        for sec, lessons in self.queue.items():
            lessons_str = (
                ", ".join([str(lesson[0]) for lesson in lessons]) if lessons else "-"
            )
            table.add_row(str(sec), lessons_str)

        return table

    def completed_table(self) -> Table:
        table = Table(title="Videos descargados", show_lines=True)
        table.add_column("Video", style="cyan")

        for v in self.completed:
            table.add_row(v)

        return table
