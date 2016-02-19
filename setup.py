#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name="gpsnetxml",
      version="1.0.0",
      author="Krzysztof Otręba",
      author_email="krzotr@gmail.com",
      download_url="https://github.com/krzotr/gpsnetxml",
      url="https://github.com/krzotr/gpsnetxml",
      long_description="""Convert gpsxml and netxml files to JSON format""",
      packages=["gpsnetxml"],
      scripts=['bin/gpsnetxml'],
      package_data={"gpsnetxml": ["asset/*.netxml",
                                  "asset/*.json",
                                  "asset/*.gpsxml",
                                  "asset/xsd/*"]},
      classifiers=["Programming Language :: Python",
                   "Topic :: Internet :: Log Analysis",
                   "Topic :: System :: Networking",
                   "Topic :: Utilities"],
      keywords="kismet gpsxml netxml wifi wpa wpa2 wep")
