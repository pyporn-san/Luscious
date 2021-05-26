import re

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = fh.read().splitlines()
with open("luscious/__init__.py", encoding='utf8') as fh:
    version = re.search(r'__version__ = "(.*?)"', fh.read()).group(1)

print(install_requires)
setuptools.setup(
    name="luscious",
    version=version,
    author="pyporn-san",
    author_email="pypornsan@gmail.com",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    install_requires=install_requires,
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities"
    ],
    python_requires='>=3.8',
)
