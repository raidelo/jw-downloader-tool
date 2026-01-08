from re import compile
from typing import Optional

from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement
from requests import Response

from utils import custom_get
from types_ import JWLessonMedia, JWSectionMediaSummary, JWVideo, LessonID, SectionID


VALID_A_TAG_TEXT = "Descargar este video"
VALID_H3_TAG_CLASS = "du-color--coolGray-500"

LESSON_NUMBER_RE = compile(r"^(\d{1,2})\s+.*")
SECTION_ALL_RE = compile(r"^all([|.](a(ll)?|m(ain)?|e(xtra)?))?$")

SECTION_MULTIMEDIA_URL = "https://www.jw.org/es/biblioteca/libros/disfrute-vida-para-siempre/seccion-%s/multimedia/"

DEFAULT_QUALITY = 720
DEFAULT_MAX_SIZE = None
DEFAULT_MAX_DURATION = None


class JWDownloader:
    """
    Downloads and parses multimedia content from JW sections.

    This class is responsible for fetching raw section data from the JW
    platform, parsing multimedia information from HTML pages, and
    optionally resolving additional video properties via the API.

    Download behavior can be configured using quality, maximum size,
    and maximum duration constraints.
    """

    def __init__(
        self,
        quality: str | int = DEFAULT_QUALITY,
        max_size: Optional[int] = DEFAULT_MAX_SIZE,
        max_duration: Optional[int] = DEFAULT_MAX_DURATION,
    ):
        """
        Initializes a `JWDownloader` instance with download constraints.

        Args:
            quality: Desired video quality. May be a string or a numeric
                identifier, depending on the platform's conventions.
            max_size: Maximum allowed video size in bytes. If `None`,
                no size limit is enforced.
            max_duration: Maximum allowed video duration in seconds.
                If `None`, no duration limit is enforced.
        """
        self.quality = quality
        self.max_size = max_size
        self.max_duration = max_duration

    @classmethod
    def _get_sect_raw(cls, section: SectionID) -> Response:
        return custom_get(SECTION_MULTIMEDIA_URL % section)

    @classmethod
    def parse_sect_data_from_html(
        cls,
        section: SectionID,
        content: bytes,
        resolve: bool,
    ) -> JWSectionMediaSummary:
        """
        Parses a section into a `JWSectionMediaSummary`.

        Args:
            section: Number of the section to parse.
            content: HTML content of the section.
            resolve: Whether to automatically resolve each video's
                properties from the API.

        Returns:
            An instance of `JWSectionMediaSummary`.
        """
        err_msg = "Could not get the corresponding data"

        soup = BeautifulSoup(content, "html.parser")

        main_tag: Optional[PageElement] = soup.find(
            name="main", attrs={"id": "content"}
        )
        if not isinstance(main_tag, Tag):
            raise ValueError(err_msg)

        nav_bar_tag: Optional[PageElement] = main_tag.find(
            name="div", attrs={"id": "tt3"}
        )
        if not isinstance(nav_bar_tag, Tag):
            raise ValueError(err_msg)

        siblings: list[PageElement] = nav_bar_tag.find_next_siblings()

        lessons: list[JWLessonMedia] = []

        in_primary, in_supplementary = False, False

        curr_lesson: Optional[JWLessonMedia] = None

        for sibling in siblings:
            if not isinstance(sibling, Tag):
                raise ValueError(err_msg)

            if sibling.name == "h2":  # is lesson title
                in_primary, in_supplementary = True, False

                lesson_title: str = sibling.text.strip()

                lesson_number: LessonID = cls._extract_lesson_number_from_title(
                    lesson_title
                )

                if isinstance(curr_lesson, JWLessonMedia):
                    lessons.append(curr_lesson)

                curr_lesson = JWLessonMedia(
                    number=lesson_number,
                    title=lesson_title,
                    primary_videos=[],
                    supplementary_videos=[],
                )

            elif in_primary and curr_lesson is not None:
                if cls._is_supplementary_subsection_header(sibling):
                    in_primary, in_supplementary = False, True
                    continue

                video_link: Optional[str] = cls._extract_video_link(sibling)
                if video_link is not None:
                    v = JWVideo(url=video_link)
                    if resolve:
                        v.resolve()
                    curr_lesson.primary_videos.append(v)

            elif in_supplementary and curr_lesson is not None:
                video_link: Optional[str] = cls._extract_video_link(sibling)
                if video_link is not None:
                    v = JWVideo(url=video_link)
                    if resolve:
                        v.resolve()
                    curr_lesson.supplementary_videos.append(v)

        if isinstance(curr_lesson, JWLessonMedia):
            lessons.append(curr_lesson)

        return JWSectionMediaSummary(
            number=section,
            lessons=lessons,
        )

    @classmethod
    def get_sect_data_parsed(
        cls,
        section: SectionID,
        resolve: bool,
    ) -> JWSectionMediaSummary:
        """
        Retrieves and parses the media summary data for a given section.

        This method fetches the raw HTML content of the section and then
        parses it into a `JWSectionMediaSummary` instance.

        Args:
            section: Identifier of the section to retrieve and parse.
            resolve: Whether to automatically resolve each video's properties
                using the API.

        Returns:
            A parsed `JWSectionMediaSummary` instance containing the media
            data for the section.
        """
        content = cls._get_sect_raw(section=section).iter_content(chunk_size=4096)

        return cls.parse_sect_data_from_html(
            section=section,
            content=bytes(content),
            resolve=resolve,
        )

    @staticmethod
    def _extract_lesson_number_from_title(title: str) -> LessonID:
        """
        Extracts the lesson number from a lesson title string.

        The lesson number is extracted using the predefined
        `LESSON_NUMBER_RE` regular expression. If no lesson number
        can be found, `0` is returned.

        Args:
            title: Title string from which the lesson number should be extracted.

        Returns:
            The extracted lesson number, or `0` if no match is found.
        """

        match = LESSON_NUMBER_RE.match(title)
        if match:
            return int(match.group(1))
        else:
            return 0

    @staticmethod
    def _is_supplementary_subsection_header(tag: Tag) -> bool:
        """
        Determines whether a tag represents a supplementary subsection header.

        A tag is considered a supplementary subsection header if it is an
        `<h3>` element and contains the expected CSS class defined by
        `VALID_H3_TAG_CLASS`.

        Args:
            tag: BeautifulSoup tag to evaluate.

        Returns:
            `True` if the tag is a supplementary subsection header,
            `False` otherwise.
        """
        if tag.name == "h3":
            css_class = tag.get("class")
            return css_class is not None and VALID_H3_TAG_CLASS in css_class
        return False

    @staticmethod
    def _extract_video_link(tag: Tag) -> Optional[str]:
        """
        Extracts a video link from a tag if a valid anchor element is present.

        The method looks for an `<a>` tag inside the given tag whose text
        matches `VALID_A_TAG_TEXT`. If found, the `href` attribute is
        returned.

        Args:
            tag: BeautifulSoup tag that may contain a video link.

        Returns:
            The extracted video URL if a valid link is found, otherwise `None`.
        """
        a_tag = tag.find("a")
        if (
            a_tag is not None
            and isinstance(a_tag, Tag)
            and a_tag.text == VALID_A_TAG_TEXT
        ):
            href = a_tag.get("href")
            return href if isinstance(href, str) else None

    # def add_sections_to_queue(self, sections: list[tuple[SectionID, SubSection]]):
    #     for section, sub_section in sections:
    #         if section < 1 or section > 4:
    #             raise InvalidSection(section)
    #         if sub_section not in SUB_SECTIONS:
    #             raise InvalidLessonSubSection(sub_section)
    #         first_lesson, last_lesson = SECTIONS[section]
    #         self.queue[section] = [
    #             (lesson, SUB_SECTIONS[sub_section])
    #             for lesson in range(first_lesson, last_lesson + 1)
    #         ]
    #
    # def add_lessons_to_queue(self, lessons: list[tuple[LessonID, SubSection]]):
    #     for lesson, sub_section in lessons:
    #         if lesson < 0 or lesson > 60:
    #             raise InvalidLesson(lesson)
    #         if sub_section not in SUB_SECTIONS:
    #             raise InvalidLessonSubSection(sub_section)
    #         for section, (first_lesson, last_lesson) in SECTIONS.items():
    #             if lesson >= first_lesson and lesson <= last_lesson:
    #                 self.queue[section].append((lesson, sub_section))
    #                 break
    #
    # def exec(self, console: Console):
    #     with Progress(console=console) as progress:
    #         for section, lessons in self.queue.items():
    #             if not lessons:
    #                 continue
    #
    #             self.to_download_queue.update([(section, OrderedDict())])
    #
    #             task = progress.add_task(
    #                 f"[bold yellow]Getting information for Section {section}",
    #                 total=None,
    #             )
    #
    #             lessons.sort()
    #
    #             section_info = self._parse_sect_data(section)
    #
    #             for lesson, sub_section in lessons:
    #                 lesson_info = section_info[lesson]
    #
    #                 if sub_section in ["all", "a"]:
    #                     pass
    #                 elif sub_section in ["main", "m"]:
    #                     lesson_info.pop("extra")
    #                 elif sub_section in ["extra", "e"]:
    #                     lesson_info.pop("main")
    #
    #                 self.to_download_queue[section].update([(lesson, lesson_info)])
    #
    #             progress.remove_task(task)
    #
    # def start_download(self, console: Console) -> list[str]:
    #     self.completed = []
    #
    #     with Progress(
    #         SpinnerColumn(),
    #         TextColumn("[bold blue]{task.description}"),
    #         BarColumn(bar_width=None),
    #         TextColumn("[green]{task.completed}/{task.total}"),
    #         "[progress.percentage]{task.percentage:>3.1f}%",
    #         "•",
    #         DownloadColumn(),
    #         "•",
    #         TransferSpeedColumn(),
    #         "•",
    #         TimeRemainingColumn(),
    #         console=console,
    #         transient=True,
    #     ) as progress:
    #         root_path = mkdirs(Path().joinpath("Disfrute de la vida para siempre!"))
    #
    #         for section, lessons in self.to_download_queue.items():
    #             if not lessons:
    #                 continue
    #
    #             console.print(f"\n[bold yellow]\u25b6 Sección {section}[/bold yellow]")
    #
    #             section_path = mkdirs(root_path.joinpath(f"Sección {section}"))
    #
    #             for _lesson, lesson_info in lessons.items():
    #                 lesson_title = lesson_info["title"]
    #
    #                 console.print(f"  [cyan]Lección {lesson_title}[/cyan]")
    #
    #                 lesson_path = mkdirs(
    #                     section_path.joinpath(rm_wrong_chars(lesson_title))
    #                 )
    #
    #                 videos: list[tuple[str, str]] = []
    #
    #                 subsection_main = lesson_info.get("main")
    #                 if subsection_main:
    #                     videos += [("main", api_link) for api_link in subsection_main]
    #
    #                 subsection_extra = lesson_info.get("extra")
    #                 if subsection_extra:
    #                     videos += [("extra", api_link) for api_link in subsection_extra]
    #
    #                 for subsection, api_link in videos:
    #                     try:
    #                         properties = self.get_video_properties_from_api(api_link)
    #                     except JSONDecodeError:
    #                         console.print(
    #                             "error: The remote server responded with an invalid response"
    #                         )
    #                         continue
    #                     try:
    #                         properties = properties["files"]["S"]["MP4"]
    #                     except KeyError:
    #                         console.print("error: Couldn't find the link for the video")
    #                         continue
    #
    #                     best_quality = self.get_best_quality_from(
    #                         properties, self.quality
    #                     )
    #                     if not best_quality:
    #                         console.print(
    #                             "Couldn't find the desired quality for the video"
    #                         )
    #                         continue
    #
    #                     size = best_quality["filesize"]
    #                     video_title = best_quality["title"]
    #                     video_url = best_quality["file"]["url"]
    #
    #                     if self.max_size != -1 and size > self.max_size:
    #                         console.print(
    #                             f'[bold gray]Ignorando vídeo: "{video_title}" Su tamaño excede el máximo permitido.[/]'
    #                         )
    #                         continue
    #                     if (
    #                         self.max_duration != -1
    #                         and best_quality["duration"] > self.max_duration
    #                     ):
    #                         console.print(
    #                             f'[bold gray]Ignorando vídeo: "{video_title}" Su duración excede el máximo permitido.[/]'
    #                         )
    #                         continue
    #
    #                     filename = rm_wrong_chars(
    #                         video_title
    #                         + "".join(Path(video_url.split("?")[0]).suffixes)
    #                     )
    #
    #                     task = progress.add_task(
    #                         f"Descargando: {video_title}", total=size
    #                     )
    #
    #                     written = 0
    #
    #                     if subsection == "main":
    #                         file_path = lesson_path.joinpath(filename)
    #                     else:  # subsection == "extra"
    #                         file_path = mkdirs(
    #                             lesson_path.joinpath("Descubra algo más")
    #                         ).joinpath(filename)
    #
    #                     for bytes_written in download_archive(
    #                         video_url, size, file_path
    #                     ):
    #                         progress.update(task, advance=bytes_written)
    #                         written += bytes_written
    #                         if written == size:
    #                             break
    #
    #                     progress.remove_task(task)
    #                     self.completed.append(video_title)
    #                     console.print(
    #                         f"    [bold][green]✔ {video_title}[/bold] descargado[/green]"
    #                     )
    #
    # @staticmethod
    # def get_best_quality_from(properties: dict, quality: int) -> dict | None:
    #     best_match, index_of_best_match = 0, None
    #     for variant_pos, variant in enumerate(properties):
    #         curr_quality = int(variant["label"].strip("pP "))
    #         if curr_quality == quality:
    #             return properties[variant_pos]
    #         elif curr_quality > best_match and curr_quality < quality:
    #             best_match, index_of_best_match = curr_quality, variant_pos
    #     if index_of_best_match:
    #         return properties[index_of_best_match]
    #     return None
    #
    # def summary_table(self) -> Table:
    #     table = Table(title="Resumen de descargas")
    #     table.add_column("Sección", justify="center", style="cyan", no_wrap=True)
    #     table.add_column("Lecciones", style="magenta")
    #
    #     for sec, lessons in self.queue.items():
    #         lessons_str = (
    #             ", ".join([str(lesson[0]) for lesson in lessons]) if lessons else "-"
    #         )
    #         table.add_row(str(sec), lessons_str)
    #
    #     return table
    #
    # def completed_table(self) -> Table:
    #     table = Table(title="Videos descargados", show_lines=True)
    #     table.add_column("Video", style="cyan")
    #
    #     for v in self.completed:
    #         table.add_row(v)
    #
    #     return table
