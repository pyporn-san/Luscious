import mimetypes
import time
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from pathlib import Path
from random import sample
from typing import List, Tuple, Union
from urllib.parse import urljoin, urlparse
from urllib.request import getproxies

import requests
from faker import Faker
from pathvalidate import sanitize_filepath
from requests import Session
from requests.adapters import HTTPAdapter
from requests.models import Response
from tqdm import trange, tqdm
from urllib3.util.retry import Retry

try:
    from queries import *
except:
    from .queries import *  # pylint: disable=unused-wildcard-import


class NotFound(Exception):
    pass


class DownloadFailed(Exception):
    pass


class albumTypeOptions(Enum):
    """
    Used as albumType for album search queries
    """
    All = "All"
    Manga = "Manga"
    Pictures = "Pictures"


class contentTypeOptions(Enum):
    """
    used as contentType in video and album search queries
    """
    All = 0
    Hentai = 2
    NonErotic = 5
    RealPeople = 6


class RequestHandler(object):
    """
    Defines a synchronous request handler class that provides methods and
    properties for working with REST APIs that is backed by the `requests`
    library.
    """
    _timeout = (5, 5)
    _total = 5
    _status_forcelist = [413, 429, 500, 502, 503, 504]
    _backoff_factor = 1
    _fake = Faker()

    def __init__(self,
                 timeout: Tuple[float, float] = _timeout,
                 total: int = _total,
                 status_forcelist: List[int] = _status_forcelist.copy(),
                 backoff_factor: int = _backoff_factor):
        """Instantiates a new request handler object."""
        self.timeout = timeout
        self.total = total
        self.status_forcelist = status_forcelist
        self.backoff_factor = backoff_factor

    @cached_property
    def retry_strategy(self) -> Retry:
        """
        The retry strategy returns the retry configuration made up of the
        number of total retries, the status forcelist as well as the backoff
        factor. It is used in the session property where these values are
        passed to the HTTPAdapter.
        """
        return Retry(total=self.total,
                     status_forcelist=self.status_forcelist,
                     backoff_factor=self.backoff_factor
                     )

    @cached_property
    def session(self) -> Session:
        """
        Creates a custom session object. A request session provides cookie
        persistence, connection-pooling, and further configuration options
        that are exposed in the RequestHandler methods in form of parameters
        and keyword arguments.
        """
        assert_status_hook = lambda response, * \
            args, **kwargs: response.raise_for_status()
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=self.retry_strategy))
        session.hooks['response'] = [assert_status_hook]
        session.headers.update({
            "User-Agent": RequestHandler._fake.chrome(version_from=80, version_to=86, build_from=4100, build_to=4200)
        })
        return session

    def get(self, url: str, params: dict = None, **kwargs) -> Response:
        """
        Returns the GET request encoded in `utf-8`. Adds proxies to this session
        on the fly if urllib is able to pick up the system's proxy settings.
        """
        response = self.session.get(
            url, timeout=self.timeout, params=params, proxies=getproxies(), **kwargs)
        response.encoding = 'utf-8'
        return response

    def post(self, url: str, params: dict = None, **kwargs) -> Response:
        """
        Returns the POST request encoded in `utf-8`. Adds proxies to this session
        on the fly if urllib is able to pick up the system's proxy settings.
        """
        response = self.session.post(
            url, timeout=self.timeout, params=params, proxies=getproxies(), **kwargs)
        response.encoding = 'utf-8'
        return response


@dataclass
class Tag():
    """
    A Tag class used to help with tags
    """
    id: str
    text: str
    category: str
    url: str

    @cached_property
    def name(self):
        """
        Returns the name of the comic without the category
        """
        return self.text.split(":")[-1].strip().title()

    @cached_property
    def fullName(self):
        """
        returns the full name of the in the format "category: name"
        """
        return self.text

    @cached_property
    def sanitizedName(self):
        """
        Returns the sanitized name of the tag
        """
        return sanitize_filepath(self.name)

    @cached_property
    def hashtag(self):
        """
        Returns the tag name in hashtag format "#Tag_Name"
        """
        return f"#{self.sanitizedName.replace(' ','_').replace('-','_')}"

    def __str__(self):
        """
        Returns the tag name
        """
        return self.name


@dataclass
class Genre():
    """
    A Tag class used to help with tags
    """
    id: str
    title: str
    url: str

    @cached_property
    def name(self):
        """
        Returns the name of the comic without the category
        """
        return self.text.split(":")[-1].strip().title()

    @cached_property
    def fullName(self):
        """
        returns the full name of the in the format "category: name"
        """
        return self.text

    @cached_property
    def sanitizedName(self):
        """
        Returns the sanitized name of the tag
        """
        return sanitize_filepath(self.name)

    @cached_property
    def hashtag(self):
        """
        Returns the tag name in hashtag format "#Tag_Name"
        """
        return f"#{self.sanitizedName.replace(' ','_').replace('-','_')}"

    def __str__(self):
        """
        Returns the tag name
        """
        return self.name


class Album():
    """
    A class representing an album and it's properties
    """

    def __init__(self, albumInput: Union[int, str, dict], download: bool = False, handler: RequestHandler = None):
        """
        Initializes an album object based on albumInput
        albumInput can either be:
        An integer, being the ablbum Id
        Example (NSFW)<https://www.luscious.net/albums/animated-gifs_374481/>'s Id being  374481

        A string, the link itself
        Some pages might not show up if you don't login using a Luscious object

        A json dict being the json response of the Album
        """
        if(not handler):
            self.__handler = RequestHandler()
        else:
            self.__handler = handler

        try:
            if(isinstance(albumInput, dict)):
                self.__json = albumInput
                self.__id = int(self.__json["id"])
            elif(isinstance(albumInput, int)):
                self.__id = albumInput
                self.__json = self.__handler.post(
                    Luscious.API, json=getAlbumInfo(self.__id)).json()["data"]["album"]["get"]
            elif(isinstance(albumInput, str)):
                self.__id = int(albumInput.split("_")[-1][:-1])
                self.__json = self.__handler.post(
                    Luscious.API, json=getAlbumInfo(self.__id)).json()["data"]["album"]["get"]
            else:
                raise TypeError
            self.__url = urljoin(Luscious.HOME, self.__json["url"])
        except:
            raise NotFound

    def __str__(self) -> str:
        """
        Returns the Album's name
        """
        return self.name

    @cached_property
    def name(self) -> str:
        """
        Returns the name of the Album
        """
        return self.__json["title"]

    @cached_property
    def sanitizedName(self) -> str:
        """
        Returns the sanitized name of the Album
        """
        return sanitize_filepath(self.name)

    @cached_property
    def id(self) -> int:
        return self.__id

    @cached_property
    def url(self) -> str:
        """
        Returns the url associated with the Album
        """
        return self.__url

    @cached_property
    def downloadUrl(self) -> str:
        """
        Returns the the download url of the Album
        """
        return urljoin(Luscious.HOME, self.json["download_url"])

    @cached_property
    def contentUrls(self) -> List[str]:
        """
        Returns the list of content associated with the Album
        """
        picsJson = self.__handler.post(Luscious.API, json=getPictures(
            self.__id)).json()["data"]["picture"]["list"]
        pics = [i["url_to_original"] for i in picsJson["items"]]
        for i in range(1, int(picsJson["info"]["total_pages"])):
            picsJson = self.__handler.post(
                Luscious.API, json=getPictures(self.__id, page=i+1)).json()
            pics += [i["url_to_original"]
                     for i in picsJson["data"]["picture"]["list"]["items"]]
        return pics

    @cached_property
    def pictureCount(self) -> int:
        """
        Returns the number of pictures in the Album(This count includes the gifs)
        """
        return self.json["number_of_pictures"]

    @cached_property
    def animatedCount(self) -> int:
        """
        Returns the number of animated pictures in the Album
        """
        return self.json["number_of_animated_pictures"]

    @cached_property
    def thumbnail(self) -> str:
        """
        Returns the url of the Album's thumbnail
        """
        return self.json["cover"]["url"]

    @cached_property
    def description(self) -> str:
        """
        Returns the description of the Album
        """
        return self.json["description"]

    @cached_property
    def genres(self) -> List[Genre]:
        """
        The Album's genres
        Returns a list of `Genre` objects
        """
        return [Genre(genre["id"], genre["title"], genre["url"]) for genre in self.json["genres"]]

    @cached_property
    def tags(self) -> List[Tag]:
        """
        The Album's tags
        Returns a list of `Tag` objects
        """
        return [Tag(tag["id"], tag["text"], tag["category"], tag["url"]) for tag in self.json["tags"]]

    @cached_property
    def artists(self) -> List[str]:
        """
        Return a list of artist names associated with the Album
        """
        return [tag.name for tag in self.tags if tag.category == "Artist"]

    @cached_property
    def characters(self) -> List[str]:
        """
        Returns the list of characters present in the Album
        """
        return [tag.name for tag in self.tags if tag.category == "Character"]

    @cached_property
    def parodies(self) -> List[Tag]:
        """
        Returns the list of parodied content names
        """
        return [tag.name for tag in self.tags if tag.category == "Parody"]

    @cached_property
    def audiences(self) -> dict:
        """
        The intended audience of the Album
        Returns a dict with fields "id", "title", "url"
        """
        return self.json["audiences"]

    @cached_property
    def ongoing(self) -> bool:
        """
        The status of the Album
        True if it's ongoing
        False if not
        Warning:
        Will return False for all non manga albums
        """
        onTag = Tag(id='1895669', text='ongoing',
                    category=None, url='/tags/ongoing/')
        return onTag in self.tags

    @cached_property
    def isManga(self) -> bool:
        """
        Returns True if the Album is a manga, False if it's a picture set
        """
        return self.json["is_manga"]

    @cached_property
    def contentType(self) -> str:
        """
        Returns the content type of the Album which is either "Manga", "Non-Erotic" or "Real People"
        """
        return self.json["content"]["title"]

    @cached_property
    def json(self) -> dict:
        """
        Returns the json response of the Album
        """
        return self.__json

    @cached_property
    def handler(self) -> RequestHandler:
        """
        Returns the handler object of the Album
        """
        return self.__handler

    def downloadContent(self, root: Union[Path, str] = Path("Albums"), printProgress: bool = True):
        """
        Downloads all pictures that don't already exist in the directory to the folder `root`
        The progress bar can be disabled by passing False to printProgress
        Returns the list of downloaded files' filepaths
        """
        paths = []
        if(isinstance(root, str)):
            root = Path(root)
        root = root.joinpath(sanitize_filepath(self.sanitizedName))
        root.mkdir(parents=True, exist_ok=True)
        with trange(len(self.contentUrls), disable=not printProgress, desc=self.name) as tq:
            for i in tq:
                if(self.isManga):
                    fpath = root.joinpath(
                        f"{self.sanitizedName}_{str(i).zfill(len(str(self.pictureCount-1)))}")
                else:
                    fpath = root.joinpath(
                        Path(urlparse(self.contentUrls[i]).path).name)
                printName = f'"{self.name}" page {i+1}/{self.pictureCount}'
                globResult = list(root.glob(f"{fpath.stem}*"))
                if(globResult):
                    tq.set_description(f"{printName} exists")
                    paths.append(globResult[0])
                    continue
                else:
                    try:
                        r = self.handler.get(self.contentUrls[i])
                        fpath = fpath.with_suffix(
                            mimetypes.guess_extension(r.headers['content-type']))
                        with open(sanitize_filepath(fpath), "wb") as f:
                            f.write(r.content)
                        tq.set_description(f'{printName} done')
                        paths.append(fpath)
                    except Exception as e:
                        with open(sanitize_filepath(fpath.with_name(fpath.name + "_SKIPPED")), "wb") as _:
                            pass
                        tq.set_description(
                            f'{printName} skipped because {e}')
                        paths.append(fpath)
        return paths


class Video():
    """
    A class representing a video and it's properties
    """

    def __init__(self, videoInput: Union[int, str, dict], download: bool = False, handler: RequestHandler = None):
        """
        Initializes an Video object based on videoInput
        videoInput can either be:
        An integer, being the Video id
        Example (NSFW)<https://luscious.net/videos/dropout_episode_1_hq_11401/>'s Id being  11401

        A string, the link itself
        Some pages might not show up if you don't login using a Luscious object

        A json dict being the json response of the Video
        """

        if(not handler):
            self.__handler = RequestHandler()
        else:
            self.__handler = handler

        try:
            if(isinstance(videoInput, dict)):
                self.__json = videoInput
                self.__id = int(self.__json["id"])
            elif(isinstance(videoInput, int)):
                self.__id = videoInput
                self.__json = self.__handler.post(
                    Luscious.API, json=getVideoInfo(self.__id)).json()["data"]["video"]["get"]
            elif(isinstance(videoInput, str)):
                self.__id = int(videoInput.split("_")[-1][:-1])
                self.__json = self.__handler.post(
                    Luscious.API, json=getVideoInfo(self.__id)).json()["data"]["video"]["get"]
            else:
                raise TypeError
            self.__url = urljoin(Luscious.HOME, self.__json["url"])
        except:
            raise NotFound

    def __str__(self) -> str:
        return self.name

    @cached_property
    def name(self) -> str:
        """
        Returns the name of the Video
        """
        return self.__json["title"]

    @cached_property
    def sanitizedName(self) -> str:
        """
        Returns the sanitized name of the Video
        """
        return sanitize_filepath(self.name)

    @cached_property
    def id(self) -> int:
        return self.__id

    @cached_property
    def url(self) -> str:
        """
        Returns the url associated with the Video
        """
        return self.__url

    @cached_property
    def contentUrls(self) -> List[str]:
        """
        Returns the list video urls in each for a different resolution of the video in increasing order

        Warning:
        Some resolutions may not exist
        """
        return [self.json["v240p"], self.json["v360p"], self.json["v720p"], self.json["v1080p"]]

    @cached_property
    def thumbnail(self) -> str:
        """
        Returns the url of the Video's thumbnail
        """
        return self.json["poster_url"]

    @cached_property
    def description(self) -> str:
        """
        Returns the description of the Video
        """
        return self.json["description"]

    @cached_property
    def genres(self) -> List[Genre]:
        """
        The Album's genres
        Returns a list of `Genre` objects
        """
        return [Genre(genre["id"], genre["title"], genre["url"]) for genre in self.json["genres"]]

    @cached_property
    def tags(self) -> List[Tag]:
        """
        The Video's tags
        Returns a list of `Tag` objects
        """
        return [Tag(tag["id"], tag["text"], tag["category"], tag["url"]) for tag in self.json["tags"]]

    @cached_property
    def audiences(self) -> dict:
        """
        The intended audience of the Video
        Returns a dict with fields "id", "title", "url"
        """
        return self.json["audiences"]

    @cached_property
    def contentType(self) -> str:
        """
        Returns the content type of the Video which is either "Hentai", "Non-Erotic" or "Real People"
        """
        return self.json["content"]["title"]

    @cached_property
    def json(self) -> dict:
        """
        Returns the json response of the Video
        """
        return self.__json

    @cached_property
    def handler(self) -> RequestHandler:
        """
        Returns the handler object of the Video
        """
        return self.__handler

    def downloadContent(self, downloadQuality: int = 0, root: Union[Path, str] = Path("Videos"), printProgress: bool = True):
        """
        FIXME for some reason access to videos are forbidden. This was not the case before. If anybody can help feel free to raise an issue or a pull request


        downloads the video if it doesn't already exist in the directory to the folder `root`
        The quality will be chosen by `downloadQuality` that defaults to the lowest quality
        `downloadQuality` can be a number from 0 to 3 with 0 representing 240p (the lowest quality)
        if the chosen quality is not available it will default to the highest quality available (which is always lower than the chosen quality)
        The progress bar can be disabled by passing False to printProgress
        Returns the path of the downloaded video
        """
        if(isinstance(root, str)):
            root = Path(root)
        root = root.joinpath(sanitize_filepath(self.sanitizedName))
        root.mkdir(parents=True, exist_ok=True)
        url = self.contentUrls[downloadQuality]
        if(not url):
            for i in range(downloadQuality+1):
                url = self.contentUrls[i] if self.contentUrls[i] else url

        fpath = root.joinpath(self.sanitizedName)
        printName = self.name
        r = self.handler.get(url, stream=True)
        fpath = fpath.with_suffix(
            mimetypes.guess_extension(r.headers['content-type']))
        total_size_in_bytes = int(
            r.headers.get('content-length', 0))
        with tqdm(total=total_size_in_bytes, disable=not printProgress, unit='iB', unit_scale=True, desc=self.name) as tq:
            with open(sanitize_filepath(fpath), 'wb') as file:
                for data in r.iter_content(1024):
                    tq.update(len(data))
                    file.write(data)
            if total_size_in_bytes != 0 and tq.n != total_size_in_bytes:
                with open(sanitize_filepath(fpath.with_name(fpath.name + "_SKIPPED")), "wb") as _:
                    pass
                tq.set_description(f'{printName} skipped')
                return fpath
            else:
                return fpath


class Luscious(RequestHandler):
    """
    A Luscious class used to for various utilities and login
    """
    API = "https://members.luscious.net/graphql/nobatch/"
    HOME = "https://members.luscious.net"
    LOGIN = "https://members.luscious.net/accounts/login/"

    def __init__(self, username: str = None, password: str = None, timeout: Tuple[float, float] = RequestHandler._timeout, total: int = RequestHandler._total, status_forcelist: List[int] = RequestHandler._status_forcelist.copy(), backoff_factor: int = RequestHandler._backoff_factor):
        """
        Initializes a Luscious object

        Pass in your <https://members.luscious.net> email and password to login and use your own genre filters
        Some genres are blocked by default and will not show up without login
        """
        super().__init__(timeout, total, status_forcelist, backoff_factor)
        self.__handler = RequestHandler(
            self.timeout, self.total, self.status_forcelist, self.backoff_factor)

        if(username and password):
            response = self.__handler.post(
                self.LOGIN, data={"login": username, "password": password, "remember": "on"})
            if("The username and/or password you specified are not correct." in response.text):
                print("Login failed. Please check your credentials")

    def getAlbum(self, albumInput: Union[int, str], download: bool = False) -> Album:
        """
        Return an `Album` object based on albumInput

        albumInput can either be an integer, being the ablbum Id
        Example (NSFW)<https://www.luscious.net/albums/animated-gifs_374481/>'s Id being  374481
        Or it can be a string, the link itself
        """
        return Album(albumInput, download, handler=self.__handler)

    def getVideo(self, videoInput: Union[int, str], download: bool = False) -> Video:
        """
        Return an `Video` object based on videoInput

        videoInput can either be an integer, being the Video id
        Example (NSFW)<https://luscious.net/videos/dropout_episode_1_hq_11401/>'s Id being  11401
        Or it can be a string, the link itself
        """
        return Video(videoInput, download, handler=self.__handler)

    def searchAlbum(self, query: str, page: int = 1, display: str = "rating_all_time", albumType: albumTypeOptions = albumTypeOptions.All, contentType: contentTypeOptions = contentTypeOptions.All) -> List[int]:
        """
        Searches <https://luscious.net> for albums with given query

        `page` is the page to search in
        `display` is the sorting option. If you need to change it look it up in the search section of the website
        `albumType` is the type of albums to search for (from the Enum albumTypeOptions)
        `contentType` is the content type to search for (from the Enum contentTypeOptions)

        Returns a result dict with 2 keys `items` and `info`

        `items` is  a list of album ids

        `info` is a dict with fields `page`, `has_next_page`, `has_previous_page`, `total_items`, `total_pages`, `items_per_page` ,`url_complete`
        """
        json = self.__handler.post(
            self.API, json=albumSearchQuery(query, page=page, display=display, albumType=albumType.value, contentType=contentType.value)).json()
        albumIds = [int(i["id"])
                    for i in json["data"]["album"]["list"]["items"]]
        return {"info": json["data"]["album"]["list"]["info"], "items": albumIds}

    def searchVideo(self, query: str, page: int = 1, display: str = "rating_all_time", contentType: contentTypeOptions = contentTypeOptions.All) -> List[int]:
        """
        Searches <https://luscious.net> for videos with given query

        `page` is the page to search in
        `display` is the sorting option. If you need to change it look it up in the search section of the website
        `contentType` is the content type to search for (from the Enum contentTypeOptions)

        Returns a result dict with 2 keys `items` and `info`

        `items` is  a list of video ids

        `info` is a dict with fields `page`, `has_next_page`, `has_previous_page`, `total_items`, `total_pages`, `items_per_page` ,`url_complete`
        """
        json = self.__handler.post(
            self.API, json=videoSearchQuery(query, page=page, display=display, contentType=contentType.value)).json()
        videoIds = [int(i["id"])
                    for i in json["data"]["video"]["list"]["items"]]
        return {"info": json["data"]["video"]["list"]["info"], "items": videoIds}

    def getLandingPage(self, limit: int = 15):
        """
        Get frontpage Albums

        Returns a dict with 3 keys: `Hentai Manga`,`Hentai Pictures` and `Porn Pictures`
        With the value of all three being a list of integer ids of their respective content
        """
        json = self.__handler.post(
            self.API, json=landingPageQuery(limit)).json()

        return {k["title"]: [int(i["id"]) for i in k["items"]]
                for k in json["data"]["landing_page_album"]["frontpage"]["sections"]}

    def getRandomId(self):
        """
        Returns a random id from latest interacted albums

        Note:
        This isn't truly random but this is the same random mechanism in the website itself
        """
        json = self.__handler.post(self.API, json=albumSearchQuery(
            "", 1, "date_last_interaction")).json()
        return int(sample(json["data"]["album"]["list"]["items"], 1)[0]["id"])  # pylint: disable=unsubscriptable-object
