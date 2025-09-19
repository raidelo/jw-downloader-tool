from argparse import ArgumentParser
from collections import OrderedDict
from pathlib import Path
from pprint import pprint

from bs4 import BeautifulSoup
import colorama
import requests

from parsing import parse_spec_to_ranges, expand_ranges
from download import descargar_archivo

BASE_URL = "https://www.jw.org/es/biblioteca/libros/disfrute-vida-para-siempre/seccion-%s/multimedia/"


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("section", choices=[str(i) for i in range(1, 5)] + ["all"])
    parser.add_argument("lessons")

    return parser.parse_args()


class JWDownloader:
    def __init__(self, sections: list[int]):
        self.sections = sections
        self.info = OrderedDict()

    def exec(self):
        for section in self.sections:
            self.info = self.__get_info_of_section(section)

    def start_download(self):
        base = Path(__file__).with_name("Disfrute de la vida para siempre!")
        base.mkdir(parents=True, exist_ok=True)

        for section in self.sections:
            print(f"Comenzando descarga de la sección {section}")

            self.download_section(section, base)

            print(f"\n✅ Sección {section} descargada con éxito.")

    def download_section(self, section: int, base_path: Path):
        raise NotImplementedError()

    @classmethod
    def __get_info_of_section(cls, section: int):
        r = requests.get(BASE_URL % section)
        soup = BeautifulSoup(r.content, "html.parser")

        main_content = soup.find("main", {"id": "content"})
        nav_bar = main_content.find("div", {"id": "tt3"})
        siblings = nav_bar.find_next_siblings()

        summary, current_lesson = OrderedDict(), ""
        in_lessons_main, in_lessons_extra = False, False

        for sibling in siblings:
            if sibling.name == "h2":
                in_lessons_main, in_lessons_extra = True, False
                current_lesson = sibling.text.strip()
                summary[current_lesson] = {"main": [], "extra": []}
                continue

            if in_lessons_main:
                if cls.__is_extra(sibling):
                    in_lessons_main, in_lessons_extra = False, True
                    continue

                video_link = cls.__get_video_link(sibling)
                if video_link:
                    summary[current_lesson]["main"].append(sibling)

            if in_lessons_extra:
                video_link = cls.__get_video_link(sibling)
                if video_link:
                    summary[current_lesson]["extra"].append(sibling)

        return summary

    @staticmethod
    def get_video_properties(api_link: str) -> dict:
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


def main():
    args = parse_args()

    jw_downloader = JWDownloader(
        [i for i in range(1, 5)] if args.section == "all" else [int(args.section)]
    )
    jw_downloader.exec()

    jw_downloader.start_download()


if __name__ == "__main__":
    main()
