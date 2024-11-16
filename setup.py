from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="iiif-downloader",
    version="0.1.0",
    author="Segolene-Albouy",
    author_email="segolene.albouy@gmail.com",
    description="A Python package to download images from IIIF manifests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Segolene-Albouy/iiif-download",
    project_urls={
        "Bug Tracker": "https://github.com/Segolene-Albouy/iiif-download/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "Pillow",
        "requests",
        "tqdm",
        "urllib3"
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'flake8',
            'black'
        ],
    },
)
