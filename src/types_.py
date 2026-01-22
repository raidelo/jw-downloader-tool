from dataclasses import dataclass
from enum import Enum
from typing import Optional, Self, TypedDict

from utils import custom_get

type SectionID = int
type LessonID = int


class VideoGroup(Enum):
    PRIMARY = "p"
    SUPPLEMENTARY = "s"
    ALL = "a"


class JWVideoPropertiesJSON(TypedDict):
    """
    Represents the raw JSON structure returned by the JW video API.

    This `TypedDict` defines the expected shape of the JSON object
    returned by the video properties API endpoint. It does not perform
    any parsing, validation, or transformation, and it does not
    represent a domain model.

    The concrete keys and value types will be added as the API is
    enumerated and documented.
    """

    pass  # TODO: implement


@dataclass
class JWVideoProperties:
    """
    Represents the domain model for a JW video.

    This dataclass stores the resolved properties of a video after
    fetching and parsing it's JSON data from the JW API. Unlike
    `JWVideoPropertiesJSON`, which only defines the raw JSON structure,
    this class is intended to hold typed, validated, and easily
    accessible attributes for use in the application.

    Attributes:
        # Concrete keys and types will be added once the API is fully enumerated.
    """

    pass  # TODO: implement

    @classmethod
    def from_json(cls, json_data: JWVideoPropertiesJSON) -> Self:
        """
        Creates a `JWVideoProperties` instance from a JSON dictionary.

        This method is responsible for converting a raw JSON object
        (typically matching `JWVideoPropertiesJSON`) into a
        `JWVideoProperties` dataclass instance with typed and
        validated attributes.

        Args:
            json_data: Raw JSON dictionary containing video properties,
                conforming to the structure defined by
                `JWVideoPropertiesJSON`.

        Returns:
            A fully populated `JWVideoProperties` instance.

        Notes:
            The JSON data should conform to the structure defined by
            `JWVideoPropertiesJSON`. Any missing or invalid fields
            may raise an exception depending on the parsing logic.
        """

        pass  # TODO: implement


@dataclass
class JWVideo:
    """
    Represents a video resource retrieved from the API.

    A `JWVideo` instance is created with a video API URL. The video
    properties are not fetched immediately and can be resolved lazily
    by calling `resolve`.

    Attributes:
        url: API URL used to retrieve the video properties.
        props: Parsed video properties. This is `None` until the
            video is resolved.
    """

    url: str
    props: Optional[JWVideoProperties] = None

    def resolve(self) -> JWVideoProperties:
        """
        Fetches and parses the video properties from the API.

        This method performs an HTTP request to the video's API URL,
        parses the JSON response into `JWVideoProperties`, stores the
        result in `props`, and returns it.

        Returns:
            The resolved `JWVideoProperties` instance.

        Raises:
            HTTPError: If the API request fails.
        """
        resp = custom_get(url=self.url)
        resp.raise_for_status()

        props: JWVideoPropertiesJSON = resp.json()
        p_props = JWVideoProperties.from_json(props)

        self.props = p_props

        return p_props

    @classmethod
    def from_api_link(cls, url: str) -> Self:
        """
        Creates and returns a resolved `JWVideo` from an API URL.

        This is a convenience constructor that creates a `JWVideo`
        instance and immediately resolves its properties.

        Args:
            url: API URL of the video.

        Returns:
            A `JWVideo` instance with its properties already resolved.
        """
        i = cls(url=url)
        _ = i.resolve()
        return i

    @property
    def is_resolved(self) -> bool:
        """Whether the video properties have been resolved."""
        return self.props is not None


@dataclass
class JWLessonMedia:
    """
    Represents the multimedia content of a lesson.

    A lesson consists of a set of primary videos that form the core
    content of the lesson, along with supplementary videos that provide
    additional or optional material.

    Attributes:
        number: Identifier of the lesson within the section.
        title: Human-readable title of the lesson.
        primary_videos: Videos that constitute the main content of
            the lesson.
        supplementary_videos: Additional videos that complement the
            lesson but are not part of its core content.
    """

    number: LessonID
    title: str
    primary_videos: list[JWVideo]
    supplementary_videos: list[JWVideo]


@dataclass
class JWSectionMediaSummary:
    """
    Summarizes the multimedia content of a section.

    A section is composed of multiple lessons, each containing its own
    set of multimedia resources. This class groups all lesson media
    information belonging to a single section.

    Attributes:
        number: Identifier of the section.
        lessons: Ordered list of lessons contained in the section.
    """

    number: SectionID
    lessons: list[JWLessonMedia]
