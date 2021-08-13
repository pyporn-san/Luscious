========
Examples
========

Here are some examples for using the library

Album example
-------------
.. code-block:: python

    from luscious import Luscious

    # Instantiate a Luscious class with you username and password(optional)
    Lus = Luscious("Your username", "your password")

    comic = Lus.getAlbum("https://www.luscious.net/albums/mavis_dracula_316573/")

    # Mavis Dracula
    print(comic)

    # ['Blowjob', 'Big Breasts', 'Double Penetration', 'Hotdogging', 'Titjob', 'Anal Sex', 'Big Ass']
    print([tag.name for tag in comic.tags])

    # Prints a url that will take you to the download page of the comic
    print(comic.downloadUrl)

Video example
-------------
.. code-block:: python

    from luscious import Luscious

    # Instantiate a Luscious class with you username and password(optional)
    Lus = Luscious("Your username", "your password")

    video = Lus.getAlbum("https://members.luscious.net/videos/3d-wolf-girl-with-you_9619/")

    # [3d] Wolf Girl With You
    print(video)

    # ['Blowjob', 'Censored', 'Pov', 'Wolfgirl', 'Vanilla', 'Creampie', 'Eng Sub']
    print([tag.name for tag in video.tags])

    # ['https://cdnvo.luscious.net/Mizer/110/4256bdb821f00e8b280db708ae58c8a89471aab7.426x240.mp4', 'https://cdnvo.luscious.net/Mizer/110/4256bdb821f00e8b280db708ae58c8a89471aab7.640x360.mp4', None, None]
    print(video.contentUrls)