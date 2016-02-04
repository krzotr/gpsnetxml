#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json

from gpsnetxml import ParseGpsxml
from gpsnetxml import ParseNetxml


class GpsnetxmlTest(unittest.TestCase):
    def test_get_networks(self):
        self.maxDiff = None

        net = ParseNetxml("asset/network.netxml")

        data = []

        for i in net.get_networks():
            data.append(i)

        expected = ""
        with open("asset/network.netxml.json") as f:
            expected = f.read()

        self.assertMultiLineEqual(
            expected, json.dumps(data, indent=4)
        )


class TestParseGpsxml(unittest.TestCase):
    def test_get_all_points(self):
        net = ParseGpsxml("asset/gpspoint.gpsxml")

        data = []

        for i in net.get_points():
            data.append(i)

        expected = ""
        with open("asset/gpspoint.gpsxml.json") as f:
            expected = f.read()

        self.assertMultiLineEqual(
            expected, json.dumps(data, indent=4)
        )

    def test_get_points_without_track(self):
        net = ParseGpsxml("asset/gpspoint.gpsxml", skip_gps_track=True)

        data = []

        for i in net.get_points():
            data.append(i)

        expected = ""
        with open("asset/gpspoint_without_track.gpsxml.json") as f:
            expected = f.read()

        self.assertMultiLineEqual(
            expected, json.dumps(data, indent=4)
        )

    def test_get_points_skip_all(self):
        net = ParseGpsxml("asset/gpspoint.gpsxml", skip_gps_track=True,
                          skip_all=True)

        data = []

        for i in net.get_points():
            data.append(i)

        expected = ""
        with open("asset/gpspoint_skip_all.json") as f:
            expected = f.read()

        self.assertMultiLineEqual(
            expected, json.dumps(data, indent=4)
        )


if __name__ == '__main__':
    unittest.main()
