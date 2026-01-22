from cli import DesiredProps
from types_ import JWLessonMedia, JWVideo, VideoGroup


def matches_desired_props(video: JWVideo, desired_props: DesiredProps) -> bool:
    raise NotImplementedError()  # TODO: implement


def download_video(video: JWVideo) -> None:
    raise NotImplementedError()  # TODO: implement


def download_videos(videos: list[JWVideo], desired_props: DesiredProps) -> None:
    for v in videos:
        if not matches_desired_props(video=v, desired_props=desired_props):
            continue

        download_video(video=v)


def download_lesson(
    lesson: JWLessonMedia,
    subsection: VideoGroup,
    desired_props: DesiredProps,
) -> None:
    if subsection is VideoGroup.ALL or subsection is VideoGroup.PRIMARY:
        download_videos(videos=lesson.primary_videos, desired_props=desired_props)

    if subsection is VideoGroup.ALL or subsection is VideoGroup.SUPPLEMENTARY:
        download_videos(videos=lesson.supplementary_videos, desired_props=desired_props)
