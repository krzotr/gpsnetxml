#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
import os

from gpsnetxml import ParseGpsxml
from gpsnetxml import ParseNetxml


def get_asset_dic():
    return os.path.dirname(os.path.realpath(__file__)) + "/asset"


class GpsnetxmlTest(unittest.TestCase):
    def test_get_networks(self):
        self.maxDiff = None

        net = ParseNetxml(get_asset_dic() + "/network.netxml")

        data = []

        for i in net.get_networks():
            data.append(i)

        expected = ""
        with open(get_asset_dic() + "/network.netxml.json") as f:
            expected = f.read()

        self.assertMultiLineEqual(
            expected, json.dumps(data, indent=4)
        )


class TestParseGpsxml(unittest.TestCase):
    def test_get_points(self):

        gps_points = {
            "gpspoint": ParseGpsxml.GPS_POINTS_ALL,
            "gpspoint_tracks": ParseGpsxml.GPS_POINTS_TRACKS,
            "gpspoint_zeros": ParseGpsxml.GPS_POINTS_ZEROS,
            "gpspoint_networks": ParseGpsxml.GPS_POINTS_NETWORKS
        }

        for filename, gps_point in gps_points.iteritems():
            gps = ParseGpsxml(get_asset_dic() + "/gpspoint.gpsxml", gps_point)

            data = []

            for i in gps.get_points():
                data.append(i)

            expected = ""
            with open(get_asset_dic() + "/" + filename + ".gpsxml.json") as f:
                expected = f.read()

            self.assertMultiLineEqual(
                expected, json.dumps(data, indent=4)
            )

    def test_get_points_invalid_parameter(self):
        self.assertRaises(Exception, ParseGpsxml,
                          get_asset_dic() + "/gpspoint.gpsxml", 0)


if __name__ == '__main__':
    unittest.main()
