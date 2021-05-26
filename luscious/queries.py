def getAlbumInfo(albumId):
    """
    Get album info query

    :param albumId: album id
    :return: Query
    """
    query = """query getAlbumInfo($id: ID!) {
        album {
            get(id: $id) {
            ... on Album {...AlbumStandard}
            ... on MutationError {errors {code message}}
            }
        }
    }
    fragment AlbumStandard on Album{id title tags is_manga content genres cover description audiences number_of_pictures number_of_animated_pictures url download_url}"""
    js = {
        "query": query,
        "variables": {"id": str(albumId)}
    }
    return js


def getVideoInfo(videoId):
    """
    Get video info query

    :param videoId: video id
    :return: Query
    """
    query = """query getVideoInfo($id: ID!) {
        video {
            get(id: $id) {
            ... on Video {...VideoStandard}
            ... on MutationError {errors {code message}}
            }
        }
    }
    fragment VideoStandard on Video{id title tags content genres description audiences url poster_url subtitle_url v240p v360p v720p v1080p}"""
    js = {
        "query": query,
        "variables": {"id": str(videoId)}
    }
    return js


def getPictures(albumId: int, page: int = 1):
    """
    list pictures query

    :param albumId: album id
    :param page: search page
    :return: Query
    """
    query = """query ListAlbumPictures($input: PictureListInput!) {
        picture {
            list(input: $input) {
                info {...pageInfo} 
                items {...PicUrls}
            }
        }
    } 
    fragment pageInfo on FacetCollectionInfo {
        page total_items total_pages items_per_page url_complete
    } 
    fragment PicUrls on Picture {
        url_to_original url_to_video url
    }
    """
    js = {
        "query": query,
        "variables": {
            "input": {
                "display": "position",
                "filters": [{"name": "album_id", "value": str(albumId)}],
                "page": page
            }
        }
    }
    return js


def albumSearchQuery(searchQuery: str, page: int = 1, display: str = "rating_all_time", albumType: str = "All", contentType: str = "0"):
    """
    Get search results for a query
    Currently the api is broken and returns extra fields

    :param searchQuery: search keyword
    :param page: initial search page
    :param display: sorting option
    :param albumType: type of album
    :param contentType: type of content to search for
    :return: Query
    """
    query = """query AlbumList($input: AlbumListInput!) {
        album {
            list(input: $input) {
                info {...FacetCollectionInfo}
                items {...AlbumMinimal}
            }
        }
    }
    fragment FacetCollectionInfo on FacetCollectionInfo {
        page has_next_page has_previous_page total_items total_pages items_per_page url_complete
    }
    fragment AlbumMinimal on Album {
        __typename id title number_of_pictures number_of_animated_pictures
    }
    """
    js = {
        "query": query,
        "variables": {
            "input": {
                "display": display,
                "filters": [
                    {
                        "name": "restrict_genres",
                        "value": "loose"
                    },
                    {
                        "name": "audience_ids",
                        "value": "+1+2+3+5+6+8+9+10"
                    },
                    {
                        "name": "album_type",
                        "value": albumType
                    },
                    {
                        "name": "search_query",
                        "value": searchQuery
                    },
                    {
                        "name": "content_id",
                        "value": contentType
                    }
                ],
                "page": page
            }
        }
    }
    return js


def videoSearchQuery(searchQuery: str, page: int = 1, display: str = "rating_all_time", contentType: int = 0):
    """
    Get search results for a query

    :param searchQuery: search keyword
    :param display: sorting option
    :param page: initial search page
    :param contentType: type of content to search for
    :return: Query
    """
    query = """query VideoList($input: AlbumListInput!) {
        video {
            list(input: $input) {
                info {...FacetCollectionInfo}
                items {...VideoMinimal}
            }
        }
    }
    fragment FacetCollectionInfo on FacetCollectionInfo {
        page has_next_page has_previous_page total_items total_pages items_per_page url_complete
    }
    fragment VideoMinimal on Video {
        __typename id title
    }
    """
    js = {
        "query": query,
        "variables": {
            "input": {
                "display": display,
                "filters": [
                    {
                        "name": "audience_ids",
                        "value": "+1+2+3+5+6+8+9+10"
                    },
                    {
                        "name": "search_query",
                        "value": searchQuery
                    },
                    {
                        "name": "content_id",
                        "value": contentType
                    }
                ],
                "page": page
            }
        }
    }
    return js


def landingPageQuery(limit: int = 15):
    """
    list landing page albums

    :param limit: limit on how many albums to find
    :return: Query
    """
    query = """query getLandingPage($LIMIT : Int){
        landing_page_album{
            frontpage(limit: $LIMIT){
                ...on LandingPage {
                sections{
                    ...on AlbumTopHits{title items}
                    ...on VideoTopHits{title}
                }
            }
                ...on MutationError {status}
            }
        }
    }
    """
    js = {
        "query": query,
        "variables": {
            "LIMIT": limit
        }
    }
    return js
