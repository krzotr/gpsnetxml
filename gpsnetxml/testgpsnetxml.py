#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
import os

from gpsnetxml import ParseGpsxml
from gpsnetxml import ParseNetxml
from gpsnetxml import DateConv


def get_asset_dic():
    return os.path.dirname(os.path.realpath(__file__)) + "/asset"


class TestDateConv(unittest.TestCase):
    def test_get_date(self):
        date = DateConv()

        self.assertEqual(date.get("Sat Nov 15 14:05:57 2014"),
                         "2014-11-15 14:05:57")

        date.set("%Y-%m-%dT%H:%M:%SZ")

        self.assertEqual(date.get("Mon Nov 16 11:22:33 2014"),
                         "2014-11-16T11:22:33Z")


class TestParseNetxml(unittest.TestCase):
    def test_metadata(self):
        net = ParseNetxml(get_asset_dic() + "/network.netxml")
        meta = net.get_metadata()

        self.assertDictEqual(meta, {
            "kismet_version": "2013.03.R0",
            "start_time": "2014-11-15 13:00:00"
        })

    def test_get_networks(self):
        self.maxDiff = None

        net = ParseNetxml(get_asset_dic() + "/network.netxml")

        data = []

        for i in net.get_networks():
            data.append(i)

        expected = ""
        with open(get_asset_dic() + "/network.netxml.json") as f:
            expected = json.loads(f.read())

        self.assertListEqual(expected, data)

    def test_ret_val(self):
        net = ParseNetxml(get_asset_dic() + "/network.netxml")

        self.assertEqual(0, net._ret_val(0, ""))
        self.assertEqual(5, net._ret_val(0, "5"))
        self.assertEqual(10, net._ret_val(0, 10))

        self.assertEqual(.0, net._ret_val(.0, ""))
        self.assertEqual(.2, net._ret_val(.0, "0.2"))
        self.assertEqual(.5, net._ret_val(.0, .5))

        self.assertEqual(True, net._ret_val(True, ""))
        self.assertEqual(True, net._ret_val(True, True))
        self.assertEqual(True, net._ret_val(True, "true"))
        self.assertEqual(True, net._ret_val(True, False))
        self.assertEqual(False, net._ret_val(True, "false"))

        self.assertEqual(False, net._ret_val(False, ""))
        self.assertEqual(True, net._ret_val(False, True))
        self.assertEqual(True, net._ret_val(False, "true"))
        self.assertEqual(False, net._ret_val(False, False))
        self.assertEqual(False, net._ret_val(False, "false"))

        self.assertEqual("", net._ret_val("", None))
        self.assertEqual("", net._ret_val("", ""))
        self.assertEqual("0", net._ret_val("", "0"))
        self.assertEqual("def", net._ret_val("def", None))
        self.assertEqual("def", net._ret_val("def", ""))
        self.assertEqual("TeST", net._ret_val("", "TeST"))


class TestParseGpsxml(unittest.TestCase):
    def test_metadata(self):
        gps = ParseGpsxml(get_asset_dic() + "/gpspoint.gpsxml")
        meta = gps.get_metadata()

        self.assertDictEqual(meta, {
            "gps_version": 5,
            "start_time": "2014-11-15 14:05:57",
            "file": "/root/kismet-log/Kismet-20141115_14-05-58.netxml"
        })

    def test_get_points(self):
        gps_points = {
            "gpspoint": ParseGpsxml.GPS_POINTS_ALL,
            "gpspoint_tracks": ParseGpsxml.GPS_POINTS_TRACKS,
            "gpspoint_zeros": ParseGpsxml.GPS_POINTS_ZEROS,
            "gpspoint_networks": ParseGpsxml.GPS_POINTS_NETWORKS
        }

        for filename, gps_point in gps_points.items():
            gps = ParseGpsxml(get_asset_dic() + "/gpspoint.gpsxml", gps_point)

            data = []

            for i in gps.get_points():
                data.append(i)

            expected = ""
            with open(get_asset_dic() + "/" + filename + ".gpsxml.json") as f:
                expected = json.loads(f.read())

            self.assertListEqual(expected, data)

    def test_get_points_invalid_parameter(self):
        self.assertRaises(Exception, ParseGpsxml,
                          get_asset_dic() + "/gpspoint.gpsxml", 0)


if __name__ == "__main__":
    import sys

    version = list(sys.version_info)[0]

    if version == 3:
        unittest.main(warnings="ignore")
    else:
        unittest.main()
