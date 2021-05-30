# Python Luscious GraphQL Wrapper

Luscious is a Python library that wraps the [luscious.net (NSFW)](https://www.luscious.net/) graphQL API. This is not an official API in any capacity. Please do not use this library to make an unreasonable amount of requests to the Luscious API.

[Documentation](https://luscious.readthedocs.io/en/stable/)

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the latest release of luscious.

```bash
pip install luscious
```

## Usage

```python
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
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[GPL V3.0](https://choosealicense.com/licenses/gpl-3.0/)
