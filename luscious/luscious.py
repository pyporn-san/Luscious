from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from random import sample
from typing import List, Tuple, Union
from urllib.parse import urljoin
from urllib.request import getproxies

import requests
from faker import Faker
from pathvalidate import sanitize_filepath
from requests import Session
from requests.adapters import HTTPAdapter
from requests.models import Response
from urllib3.util.retry import Retry

try:
    from queries import *
except:
    from .queries import *  # pylint: disable=unused-wildcard-import


class typeOptions(Enum):
    """
    Used as albumType for search queries
    """
    All = "All"
    Manga = "Manga"
    Pictures = "Pictures"


class RequestHandler(object):
    """
    RequestHandler
    ==============
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


class Album():
    def __init__(self, albumInput: Union[int, str, dict], download: bool = False, handler: RequestHandler = None):
        """
        Initializes an album object based on albumInput
        albumInput can either be:
        An integer, being the ablum Id
        Example (NSFW)<https://www.luscious.net/albums/animated-gifs_374481/>'s Id being  374481

        A string, the link itself
        Some pages might not show up if you don't login using a Luscious object

        A json dict being the json reponse of the Album
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
        except:
            self.__exists = False
            return

        self.__exists = True
        self.__url = urljoin(Luscious.HOME, self.__json["url"])

    def __str__(self) -> str:
        """
        Returns the Album's name
        """
        return self.name

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
    def thumbnail(self) -> str:
        """
        Returns the url of the Album's thumbnail
        """
        return self.json["cover"]["url"]

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
    def description(self) -> str:
        """
        Returns the description of the Album
        """
        return self.json["description"]

    @cached_property
    def pictureCount(self) -> int:
        """
        Returns the number of pictures in the Album
        """
        return self.json["number_of_pictures"]

    @cached_property
    def animatedCount(self) -> int:
        """
        Returns the number of animated pictures in the Album
        """
        return self.json["number_of_animated_pictures"]

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
    def exists(self) -> bool:
        """
        Returns a boolean value indicating wheter the Album exists
        """
        try:
            return all([self.__exists == True, any([self.pictureCount, self.animatedCount])])
        except:
            return False

    @cached_property
    def isManga(self) -> bool:
        """
        Returns True if the Album is a manga, False if it's a picure set
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
        Returns the json reponse of the Album
        """
        return self.__json

    @cached_property
    def handler(self) -> RequestHandler:
        """
        Returns the handler object of the Album
        """
        return self.__handler


class Video():
    def __init__(self, videoInput: Union[int, str, dict], download: bool = False, handler: RequestHandler = None):
        """
        Initializes an Video object based on videoInput
        videoInput can either be:
        An integer, being the Video id
        Example (NSFW)<https://luscious.net/videos/dropout_episode_1_hq_11401/>'s Id being  11401

        A string, the link itself
        Some pages might not show up if you don't login using a Luscious object

        A json dict being the json reponse of the Video
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
        except Exception as e:
            self.__exists = False
            print(e)
            return

        self.__exists = True
        self.__url = urljoin(Luscious.HOME, self.__json["url"])

    def __str__(self):
        return self.name

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
        # FIXME
        return self.json["poster_url"]

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
    def url(self) -> str:
        """
        Returns the url associated with the Video
        """
        return self.__url

    @cached_property
    def description(self) -> str:
        """
        Returns the description of the Video
        """
        return self.json["description"]

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
    def exists(self) -> bool:
        """
        Returns a boolean value indicating wheter the Video exists
        """
        try:
            return self.__exists == True
        except:
            return False

    @cached_property
    def contentType(self) -> str:
        """
        Returns the content type of the Video which is either "Hentai", "Non-Erotic" or "Real People"
        """
        return self.json["content"]["title"]

    @cached_property
    def json(self) -> dict:
        """
        Returns the json reponse of the Video
        """
        return self.__json

    @cached_property
    def handler(self) -> RequestHandler:
        """
        Returns the handler object of the Video
        """
        return self.__handler


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

        albumInput can either be an integer, being the ablum Id
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

    def searchAlbum(self, query: str, page: int = 1, display: str = "rating_all_time", albumType: typeOptions = typeOptions.All, returnAlbum: bool = False) -> Union[List[int], List[Album]]:
        """
        Searches <https://luscious.net> for given query

        `page` is the page to search in
        `display` is the sorting option. If you need to change it look it up in the search section of the website
        `albumType` is the type of albums to search for
        `returnAlbum` indicated the return type

        Returns a result dict with 2 keys `items` and `info`

        `items` is  a list of album ids if returnAlbum is false
        or it's a list of `Album` if returnAlbum is true

        `info` is a dict with fields `page`, `has_next_page`, `has_previous_page`, `total_items`, `total_pages`, `items_per_page` ,`url_complete`
        """
        json = self.__handler.post(
            self.API, json=albumSearchQuery(query, page=page, display=display, albumType=albumType.value)).json()

        albumIds = [int(i["id"])
                    for i in json["data"]["album"]["list"]["items"]]
        if(returnAlbum):
            albumIds = [Album(int(i)) for i in albumIds]
        return {"info": json["data"]["album"]["list"]["info"], "items": albumIds}

    def getLandingPage(self, limit: int = 15, returnAlbum: bool = False):
        """
        Get frontpage Albums

        Returns a dict with 3 keys: `Hentai Manga`,`Hentai Pictures` and `Porn Pictures`
        With the value of all three being either:
        1. A list of integer ids of their respective content, if returnAlbum is False (default)
        2. A list of `Album` instances if returnAlbum is True
        """
        json = self.__handler.post(
            self.API, json=landingPageQuery(limit)).json()
        sections = json["data"]["landing_page_album"]["frontpage"]["sections"]
        if(returnAlbum):
            dic = {k["title"]: [self.getAlbum(
                int(i["id"])) for i in k["items"]] for k in sections}
        else:
            dic = {k["title"]: [int(i["id"]) for i in k["items"]]
                   for k in sections}
        return dic

    def getRandomId(self):
        """
        Returns a random id from latest interacted albums

        Note:
        This isn't truly random but this is the same random mechanism in the website itself
        """
        json = self.__handler.post(self.API, json=albumSearchQuery(
            "", 1, "date_last_interaction")).json()
        return int(sample(json["data"]["album"]["list"]["items"], 1)[0]["id"])  # pylint: disable=unsubscriptable-object
