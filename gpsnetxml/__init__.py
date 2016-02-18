#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import xml.etree.ElementTree as et

from collections import OrderedDict

__version__ = "1.0.0"


class DateConv(object):
    """
    Convert datetime e.g. Sat Nov 15 14:05:57 2014 to 2014-11-15 14:05:57
    """

    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, date_format=None):
        if date_format is None:
            date_format = DateConv.DATE_FORMAT

        self._date_format = date_format

    def set(self, date_format):
        self._date_format = date_format

    def get(self, dt):
        date_time = time.strptime(dt, "%a %b %d %H:%M:%S %Y")

        return time.strftime(self._date_format, date_time)


class ParseGpsxml(object):
    """
    Convert .gpsxml file to json format. Based on dumpfile_gpsxml.cc
    """

    GPS_POINTS_NETWORKS = 1
    GPS_POINTS_TRACKS = 2
    GPS_POINTS_ZEROS = 4
    GPS_POINTS_ALL = 7

    def __init__(self, file, gps_points=None, date_format=None):
        self._dc = DateConv(date_format)

        self._file = file

        if gps_points is None:
            gps_points = ParseGpsxml.GPS_POINTS_ALL

        if gps_points < 1 or gps_points > ParseGpsxml.GPS_POINTS_ALL:
            raise Exception("Ïnvalid gps_points parameter")

        self._gps_points = gps_points

    def get_metadata(self):
        """
        Get metadata like gps_version, start_time and file
        """

        try:
            out = {}
            for event, el in et.iterparse(self._file, events=("start", "end")):

                # First element
                if el.tag == "gps-run":
                    attr = el.attrib
                    out["gps_version"] = int(attr["gps-version"])
                    out["start_time"] = self._dc.get(attr["start-time"])
                    el.clear()
                    continue

                # Second (last) element
                if el.tag == "network-file":
                    out["file"] = el.text
                    el.clear()
                    return out
        except:
            return {}

    def get_points(self):
        """
        Generator, return dictionary of gps point
        """

        for event, el in et.iterparse(self._file, events=("start", "end")):
            if el.tag != "gps-point":
                continue

            if event != "start":
                continue

            attr = el.attrib

            if (attr["bssid"] == "GP:SD:TR:AC:KL:OG"
                and not (self._gps_points & ParseGpsxml.GPS_POINTS_TRACKS)):
                el.clear()
                continue

            if (attr["bssid"] == "00:00:00:00:00:00"
                and attr["source"] == "00:00:00:00:00:00"
                and not (self._gps_points & ParseGpsxml.GPS_POINTS_ZEROS)):
                el.clear()
                continue

            if (attr["bssid"] != "GP:SD:TR:AC:KL:OG"
                and attr["bssid"] != "00:00:00:00:00:00"
                and attr["source"] != "00:00:00:00:00:00"
                and not (self._gps_points & ParseGpsxml.GPS_POINTS_NETWORKS)):
                el.clear()
                continue

            # Common for all gps_points types
            out = OrderedDict((
                ("bssid", attr["bssid"]),
            ))

            if attr["bssid"] != "GP:SD:TR:AC:KL:OG":
                out.update(OrderedDict((
                    ("source", attr.get("source")),
                )))

            # Common for all gps_point types
            out.update(OrderedDict((
                ("time_sec", int(attr.get("time-sec", 0))),
                ("time_usec", int(attr.get("time-usec", 0))),
                ("lat", float(attr.get("lat", .0))),
                ("lon", float(attr.get("lon", .0))),
                ("spd", float(attr.get("spd", .0))),
                ("heading", float(attr.get("heading", .0))),
                ("fix", int(attr.get("fix", 0))),
                ("alt", float(attr.get("alt", .0))),
                ("hdop", float(attr.get("hdop", .0))),
                ("vdop", float(attr.get("vdop", .0)))
            )))

            if attr["bssid"] != "GP:SD:TR:AC:KL:OG":
                out.update(OrderedDict((
                    ("signal_rssi", int(attr.get("signal_rssi", 0))),
                    ("noise_rssi", int(attr.get("noise_rssi", 0))),
                    ("signal_dbm", int(attr.get("signal_dbm", 0))),
                    ("noise_dbm", int(attr.get("noise_dbm", 0)))
                )))

            el.clear()

            yield out


class ParseNetxml(object):
    """
    Convert .netxml file to json format. Based on dumpfile_netxml.cc
    """

    gps_info_elements = ("min-lat", "min-lon", "min-alt", "min-spd",
                         "max-lat", "max-lon", "max-alt", "max-spd",
                         "peak-lat", "peak-lon", "peak-alt",
                         "avg-lat", "avg-lon", "avg-alt")

    snr_elements = ("last_signal_dbm", "last_noise_dbm", "last_signal_rssi",
                    "last_noise_rssi",
                    "min_signal_dbm", "min_noise_dbm", "min_signal_rssi",
                    "min_noise_rssi",
                    "max_signal_dbm", "max_noise_dbm", "max_signal_rssi",
                    "max_noise_rssi")

    packets_elements = ("LLC", "data", "crypt", "total", "fragments", "retries")

    def __init__(self, file, date_format=None):
        self._dc = DateConv(date_format)

        self._file = file
        self._netxml = et.parse(self._file)

    def get_metadata(self):
        """
        Get metadata like kismet_version and start_time
        """

        try:
            for event, el in et.iterparse(self._file, events=("start", "end")):
                attr = el.attrib

                return {
                    "kismet_version": attr["kismet-version"],
                    "start_time": self._dc.get(attr["start-time"])
                }
        except:
            pass

        return {}

    def _ret_val(self, default, val):
        """
        Typecast to type of first parameter
        """

        if not val or val is None:
            return default

        tp = type(default)

        if tp == int:
            return int(val)

        if tp == float:
            return float(val)

        if tp == bool:
            if type(val) == bool:
                return val

            return True if val.lower() == "true" else False

        return str(val)

    def _get_xml_attrib(self, xml_element, attrib_name, default=""):
        """
        Get attribute value from specified attribute name
        """

        try:
            val = xml_element.attrib.get(attrib_name, default)

            return self._ret_val(default, val)
        except:
            return default

    def _get_xml_element_value(self, xml_element, element_name, default=""):
        """
        Get element value from specified node
        """

        try:
            if "/" in element_name:
                index = element_name.index("/")
                e1_name = element_name[0:index]
                e2_name = element_name[index+1:]

                val = xml_element.findall(e1_name)[0].findall(e2_name)[0].text
            else:
                val = xml_element.findall(element_name)[0].text

            return self._ret_val(default, val)
        except:
            return default

    def _get_xml_values(self, node, element_name):
        """
        Get element values from specified node
        """

        try:
            ret = []

            for val in node.findall(element_name):
                ret.append(val.text.strip(" "))

            return ret
        except:
            pass

        return ()

    def _get_freqmhz(self, node):
        """
        Parse freqmhz element
        """

        try:
            freqmhz = {}

            for freq in node.findall("freqmhz"):
                f = freq.text.split(" ")
                freqmhz[f[0]] = int(f[1])

            return freqmhz
        except:
            pass

        return {}

    def _get_cloaked(self, node):
        """
        Wireless is cloaked or no
        """

        essid = node.findall("essid")

        if not essid:
            return False

        return self._get_xml_attrib(essid[0], "cloaked", False)

    def _get_multiple_values(self, node, elements, element, default):
        out = OrderedDict()

        for el in elements:
            out[el.lower().replace("-", "_")] = self._get_xml_element_value(
                node, element + "/" + el, default)

        return out

    def _get_dot11d(self, node):
        """
        Get dot11 attributes
        """

        try:
            dot11d = node.findall("dot11d")[0]
        except:
            return {}

        out = {}

        out["country"] = self._get_xml_attrib(dot11d, "country").strip(" ")
        out["range"] = []

        try:
            for d in dot11d.findall("dot11d-range"):
                out["range"].append(OrderedDict([
                    ("start", self._get_xml_attrib(d, "start", 0)),
                    ("end", self._get_xml_attrib(d, "end", 0)),
                    ("max_power", self._get_xml_attrib(d, "max-power", 0)),
                ]))
        except:
            pass

        return out

    def _get_tags(self, node):
        out = {}

        for t in node.findall("tag"):
            name = self._get_xml_attrib(t, "name", "")

            out[name] = t.text.strip(" ")

        return out

    def _get_gpsinfo(self, node):
        """
        Get whole gps-info element
        """

        return self._get_multiple_values(node, self.gps_info_elements,
                                         "gps-info", .0)

    def _get_snr(self, node):
        """
        Get whole snr-info element
        """

        return self._get_multiple_values(node, self.snr_elements, "snr-info", 0)

    def _get_packets(self, node):
        """
        Get whole packets element
        """

        return self._get_multiple_values(node, self.packets_elements,
                                         "packets", 0)

    def _get_seencards(self, node):
        """
        Get whole seen-card element
        """

        try:
            seencards = {}

            for card in node.findall("seen-card"):
                uuid = self._get_xml_element_value(card, "seen-uuid", "")

                if not uuid:
                    continue

                seencards[uuid] = {
                    "time": self._dc.get(self._get_xml_element_value(
                        card, "seen-time", "")),
                    "packets": self._get_xml_element_value(
                        card, "seen-packets", 0)
                }

            return seencards
        except:
            pass

        return {}

    def _get_ipaddress(self, node):
        """
        Get ip-address element
        """

        try:
            ip = node.findall("ip-address")[0]

            return OrderedDict((
                ("ip_type", self._get_xml_attrib(ip, "type", "Unknown")),
                ("ip_block", self._get_xml_element_value(ip, "ip-block")),
                ("ip_netmask", self._get_xml_element_value(ip, "ip-netmask")),
                ("ip_gateway", self._get_xml_element_value(ip, "ip-gateway")),
            ))
        except:
            pass

        return {}

    """Get SSIDS in wireless-network element"""
    def get_network_ssids(self, node):
        try:
            ssids = []

            for ssid in node.findall("SSID"):
                ssids.append(OrderedDict((
                    ("first_time", self._dc.get(
                        self._get_xml_attrib(ssid, "first-time"))),
                    ("last_time", self._dc.get(
                        self._get_xml_attrib(ssid, "last-time"))),
                    ("type", self._get_xml_element_value(ssid, "type")),
                    ("max_rate", self._get_xml_element_value(
                        ssid, "max-rate", .0)),
                    ("packets", self._get_xml_element_value(
                        ssid, "packets", 0)),

                    ("beaconrate", self._get_xml_element_value(
                        ssid, "beaconrate", 0)),

                    # Since Kismet-2016.01.R1
                    ("wps", self._get_xml_element_value(ssid, "wps", "No")),
                    ("wps_manuf", self._get_xml_element_value(
                        ssid, "wps-manuf")),
                    ("dev_name", self._get_xml_element_value(ssid, "dev-name")),
                    ("model_name", self._get_xml_element_value(
                        ssid, "model-name")),
                    ("model_num", self._get_xml_element_value(
                        ssid, "model-num")),

                    ("encryption", self._get_xml_values(ssid, "encryption")),

                    # Since Kismet-2016.01.R1
                    ("wpa_version", self._get_xml_element_value(
                        ssid, "wpa-version")),

                    ("dot11d", self._get_dot11d(ssid)),

                    ("essid", self._get_xml_element_value(ssid, "essid", "")),
                    ("cloaked", self._get_cloaked(ssid)),

                    ("info", self._get_xml_element_value(ssid, "info", ""))
                )))
        except:
            pass

        return ssids

    def _get_client_ssids(self, node):
        """
        Parse SSIDS from wireless-client element
        """

        try:
            ssids = []

            for ssid in node.findall("SSID"):
                ssids.append(OrderedDict((
                    ("first_time", self._dc.get(
                        self._get_xml_attrib(ssid, "first-time", ""))),
                    ("last_time", self._dc.get(
                        self._get_xml_attrib(ssid, "last-time", ""))),
                    ("type", self._get_xml_element_value(ssid, "type", "")),
                    ("max_rate", self._get_xml_element_value(
                        ssid, "max-rate", .0)),
                    ("packets", self._get_xml_element_value(
                        ssid, "packets", 0)),
                    ("beaconrate", self._get_xml_element_value(
                        ssid, "beaconrate", 0)),

                    ("dot11d", self._get_dot11d(ssid)),
                    ("encryption", self._get_xml_values(ssid, "encryption")),

                    # Rename ssid to essid
                    ("essid", self._get_xml_element_value(ssid, "ssid", "")),
                    ("info", self._get_xml_element_value(ssid, "info", "")),
                )))

            return ssids
        except:
            pass

        return ()

    def _get_bsstimestamp(self, node):
        """
        Fix for Bsstimestamp unsigned int 64
        """
        bss = self._get_xml_element_value(node, "bsstimestamp", 0)

        if bss > 9223372036854775807 or bss < -9223372036854775808:
            return 0

        return bss

    def _get_network(self, node, is_client=False):
        """
        Parse wireless-network or wireless-client
        """

        # Parse wireless-network
        if not is_client:
            return OrderedDict((
                ("number", self._get_xml_attrib(node, "number", 0)),
                ("type", self._get_xml_attrib(node, "type", "unknown")),
                ("first_time", self._dc.get(
                    self._get_xml_attrib(node, "first-time"))),
                ("last_time", self._dc.get(
                    self._get_xml_attrib(node, "last-time"))),
                ("ssids", self.get_network_ssids(node)),

                ("bssid", self._get_xml_element_value(node, "BSSID")),
                ("manuf", self._get_xml_element_value(node, "manuf")),
                ("channel", self._get_xml_element_value(node, "channel", 0)),
                ("freqmhz", self._get_freqmhz(node)),
                ("maxseenrate", self._get_xml_element_value(
                    node, "maxseenrate", 0)),

                ("carrier", self._get_xml_values(node, "carrier")),
                ("encoding", self._get_xml_values(node, "encoding")),

                ("packets", self._get_packets(node)),
                ("datasize", self._get_xml_element_value(node, "datasize", 0)),

                ("snr_info", self._get_snr(node)),
                ("gps_info", self._get_gpsinfo(node)),

                ("tag", self._get_tags(node)),

                ("ip_address", self._get_ipaddress(node)),
                ("bsstimestamp", self._get_bsstimestamp(node)),
                ("cdp_device", self._get_xml_element_value(node, "cdp-device")),
                ("cdp_portid", self._get_xml_element_value(node, "cdp-portid")),

                ("dhcp_hostname", self._get_xml_element_value(
                    node, "dhcp-hostname")),
                ("dhcp_vendor", self._get_xml_element_value(
                    node, "dhcp-vendor")),

                ("seen_cards", self._get_seencards(node)),
            ))
        # wireless-client
        else:
            return OrderedDict((
                ("number", self._get_xml_attrib(node, "number", 0)),
                ("type", self._get_xml_attrib(node, "type", "unknown")),
                ("first_time", self._dc.get(
                    self._get_xml_attrib(node, "first-time"))),
                ("last_time", self._dc.get(
                    self._get_xml_attrib(node, "last-time"))),
                ("client_mac", self._get_xml_element_value(
                    node, "client-mac")),
                ("client_manuf", self._get_xml_element_value(
                    node, "client-manuf")),
                ("ssids", self._get_client_ssids(node)),
                ("channel", self._get_xml_element_value(
                    node, "channel", 0)),
                ("freqmhz", self._get_freqmhz(node)),
                ("maxseenrate", self._get_xml_element_value(
                    node, "maxseenrate", .0)),

                ("carrier", self._get_xml_values(node, "carrier")),
                ("encoding", self._get_xml_values(node, "encoding")),

                ("packets", self._get_packets(node)),
                ("datasize", self._get_xml_element_value(
                    node, "datasize", 0)),

                ("snr_info", self._get_snr(node)),
                ("gps_info", self._get_gpsinfo(node)),
                ("ip_address", self._get_ipaddress(node)),

                ("cdp_device", self._get_xml_element_value(
                    node, "cdp-device")),
                ("cdp_portid", self._get_xml_element_value(
                    node, "cdp-portid")),

                ("dhcp_hostname", self._get_xml_element_value(
                    node, "dhcp-hostname")),
                ("dhcp_vendor", self._get_xml_element_value(
                    node, "dhcp-vendor")),

                ("seen_cards", self._get_seencards(node)),

                ("tag", self._get_tags(node)),
            ))

    def get_networks(self):
        """
        Generator, return dictionary of network
        """

        for net in self._netxml.findall("wireless-network"):
            network_json = self._get_network(net, False)

            clients = []

            # wireless-client
            for client in net.findall("wireless-client"):
                client_json = self._get_network(client, True)

                clients.append(client_json)

            network_json["wireless_clients"] = clients

            yield network_json
