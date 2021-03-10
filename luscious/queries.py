def getInfo(albumId):
    """
    Get album info query
    :param albumId: album id
    :return: Query
    """
    query = """query AlbumGetInfo($id: ID!) {
        album {
            get(id: $id) {
            ... on Album {...AlbumStandard}
            ... on MutationError {errors {code message}}
            }
        }
    }
    fragment AlbumStandard on Album{id title tags is_manga content genres audiences number_of_pictures number_of_animated_pictures url download_url}"""
    js = {
        "query": query,
        "variables": {"id": str(albumId)}
    }
    return js


def getPictures(albumId: int, page: int = 1):
    """
    list pcitures query
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


def searchQuery(searchQuery: str, page: int = 1, display: str = "rating_all_time"):
    """
    Get search results for a query
    Currently the api is broken and returns extra fields
    :param searchQuery: search keyword
    :param display: sorting option
    :param page: initial search page
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
                        "value": "pictures"
                    },
                    {
                        "name": "search_query",
                        "value": searchQuery
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
