#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import xml.etree.ElementTree as et

from collections import OrderedDict


class ParseGpsxml(object):
    """Based on dumpfile_gpsxml.cc"""

    def __init__(self, file, skip_gps_track=False, skip_all=False):
        self._file = file
        self._skip_gps_track = skip_gps_track
        self._skip_all = skip_all

        if self._skip_all:
            self._skip_gps_track = True

    def get_points(self):
        for event, el in et.iterparse(self._file, events=("start", "end")):
            if el.tag != "gps-point":
                continue

            if event != "start":
                continue

            attr = el.attrib

            if attr["bssid"] == "GP:SD:TR:AC:KL:OG" and self._skip_gps_track:
                continue

            if self._skip_all and attr["bssid"] == "00:00:00:00:00:00" \
                    and attr["source"] == "00:00:00:00:00:00":
                continue

            out = OrderedDict([
                ("bssid", attr["bssid"])
            ])

            if attr["bssid"] != "GP:SD:TR:AC:KL:OG":
                out.update(OrderedDict([
                    ("source", attr.get("source"))
                ]))

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
                    ("signal_rssi", attr.get("signal_rssi", 0)),
                    ("noise_rssi", attr.get("noise_rssi", 0)),
                    ("signal_dbm", attr.get("signal_dbm", 0)),
                    ("noise_dbm", attr.get("noise_dbm", 0))
                )))

            yield out


class ParseNetxml(object):
    """Based on dumpfile_netxml.cc"""

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

    def __init__(self, file):
        self._file = file
        self._netxml = et.parse(self._file)

    """Typecast to type of first parameter"""
    def ret_val(self, default, val):
        tp = type(default)

        if tp == int:
            return int(val)

        if tp == float:
            return float(val)

        if tp == bool:
            return json.loads(val)

        return str(val)

    """Get attribute value from specified attribute name"""
    def get_xml_attrib(self, xml_element, attrib_name, default=""):
        try:
            val = xml_element.attrib.get(attrib_name, default)

            return self.ret_val(default, val)
        except:
            return default

    """Get element value from specified node"""
    def get_xml_element_value(self, xml_element, element_name, default=""):
        try:
            if "/" in element_name:
                index = element_name.index("/")
                e1_name = element_name[0:index]
                e2_name = element_name[index+1:]

                val = xml_element.findall(e1_name)[0].findall(e2_name)[0].text
            else:
                val = xml_element.findall(element_name)[0].text

            return self.ret_val(default, val)
        except:
            return default

    """Get element values from specified node"""
    def get_xml_values(self, node, element_name):
        ret = []

        try:
            for val in node.findall(element_name):
                ret.append(val.text.strip(" "))
        except:
            pass

        return ret

    """Parse freqmhz elements"""
    def get_freqmhz(self, node):
        freqmhz = {}
        try:
            for freq in node.findall("freqmhz"):
                f = freq.text.split(" ")
                freqmhz[f[0]] = int(f[1])
        except:
            pass

        return freqmhz

    """Wireless is cloaked or no"""
    def get_cloaked(self, node):
        essid = node.findall("essid")

        if not essid:
            return False

        return self.get_xml_element_value(essid[0], "cloaked", False)

    def _get_multiple_values(self, node, elements, element, default):
        out = OrderedDict()

        for el in elements:
            out[el.lower()] = self.get_xml_element_value(
                node, element + "/" + el, default)

        return out

    """Get whole gps-info element"""
    def get_gpsinfo(self, node):
        return self._get_multiple_values(node, self.gps_info_elements,
                                         "gps-info", .0)

    """Get whole snr-info element"""
    def get_snr(self, node):
        return self._get_multiple_values(node, self.snr_elements, "snr-info", 0)

    """Get whole packets element"""
    def get_packets(self, node):
        return self._get_multiple_values(node, self.packets_elements,
                                         "packets", 0)

    """Get whole seen-card element"""
    def get_seencards(self, node):
        seencards = {}

        try:
            for card in node.findall("seen-card"):
                uuid = self.get_xml_element_value(card, "seen-uuid", "")

                if not uuid:
                    continue

                seencards[uuid] = {
                    "time": self.get_xml_element_value(card, "seen-time", ""),
                    "packets": self.get_xml_element_value(card,
                                                          "seen-packets", 0)
                }
        except:
            pass

        return seencards

    """Get ip-address element"""
    def get_ipaddress(self, node):
        try:
            ip = node.findall("ip-address")[0]

            return OrderedDict((
                ("ip_type", self.get_xml_attrib(ip, "type", "Unknown")),
                ("ip_block", self.get_xml_element_value(ip, "ip-block")),
                ("ip_netmask", self.get_xml_element_value(ip, "ip-netmask")),
                ("ip_gateway", self.get_xml_element_value(ip, "ip-gateway")),
            ))
        except:
            return {}

    """Get SSIDS in wireless-network element"""
    def get_network_ssids(self, node):
        ssids = []
        try:
            for ssid in node.findall("SSID"):
                ssids.append(OrderedDict((
                    ("first_time", self.get_xml_attrib(ssid, "first-time")),
                    ("last_time", self.get_xml_attrib(ssid, "last-time")),
                    ("type", self.get_xml_element_value(ssid, "type")),
                    ("max_rate", self.get_xml_element_value(
                        ssid, "max-rate", .0)),
                    ("packets", self.get_xml_element_value(ssid, "packets", 0)),

                    ("beaconrate", self.get_xml_element_value(
                        ssid, "beaconrate", 0)),

                    ("wps", self.get_xml_element_value(ssid, "wps", "No")),
                    ("wps_manuf", self.get_xml_element_value(
                        ssid, "wps-manuf")),
                    ("dev_name", self.get_xml_element_value(ssid, "dev-name")),
                    ("model_name", self.get_xml_element_value(
                        ssid, "model-name")),
                    ("model_num", self.get_xml_element_value(
                        ssid, "model-num")),

                    ("encryption", self.get_xml_values(ssid, "encryption")),
                    ("wpa_version", self.get_xml_element_value(
                        ssid, "wpa-version")),

                    # @todo
                    ("dot11d", {}),

                    ("essid", self.get_xml_element_value(ssid, "essid", "")),
                    ("cloaked", self.get_cloaked(ssid)),

                    ("info", self.get_xml_element_value(ssid, "info", ""))
                )))
        except:
            pass

        return ssids

    """Parse SSIDS from wireless-client element"""
    def get_client_ssids(self, node):
        ssids = []
        try:
            for ssid in node.findall("SSID"):
                ssids.append(OrderedDict((
                    ("first_time", self.get_xml_attrib(ssid, "first-time", "")),
                    ("last_time", self.get_xml_attrib(ssid, "last-time", "")),
                    ("type", self.get_xml_element_value(ssid, "type", "")),
                    ("max_rate", self.get_xml_element_value(
                        ssid, "max-rate", .0)),
                    ("packets", self.get_xml_element_value(
                        ssid, "packets", 0)),
                    ("beaconrate", self.get_xml_element_value(
                        ssid, "beaconrate", 0)),

                    # @todo
                    ("dot11d", {}),
                    ("encryption", self.get_xml_values(ssid, "encryption")),

                    ("essid", self.get_xml_element_value(ssid, "ssid", "")),
                    ("info", self.get_xml_element_value(ssid, "info", "")),
                )))
        except:
            pass

        return ssids

    """Parse wireless-network or wireless-client"""
    def get_network(self, node, is_client=False):
        # Parse wireless-network
        if not is_client:
            return OrderedDict((
                ("number", self.get_xml_attrib(node, "number", 0)),
                ("type", self.get_xml_attrib(node, "type", "unknown")),
                ("first_time", self.get_xml_attrib(node, "first-time")),
                ("last_time", self.get_xml_attrib(node, "last-time")),
                ("ssids", self.get_network_ssids(node)),

                ("bssid", self.get_xml_element_value(node, "BSSID")),
                ("manuf", self.get_xml_element_value(node, "manuf")),
                ("channel", self.get_xml_element_value(node, "channel", 0)),
                ("freqmhz", self.get_freqmhz(node)),
                ("maxseenrate", self.get_xml_element_value(
                    node, "maxseenrate", 0)),

                ("carrier", self.get_xml_values(node, "carrier")),
                ("encoding", self.get_xml_values(node, "encoding")),

                ("packets", self.get_packets(node)),
                ("datasize", self.get_xml_element_value(node, "datasize", 0)),

                ("snr_info", self.get_snr(node)),
                ("gps_info", self.get_gpsinfo(node)),

                # @todo
                ("tag", []),

                ("ip_address", self.get_ipaddress(node)),
                ("bsstimestamp", self.get_xml_element_value(
                    node, "bsstimestamp", 0)),
                ("cdp_device", self.get_xml_element_value(node, "cdp-device")),
                ("cdp_portid", self.get_xml_element_value(node, "cdp-portid")),

                ("dhcp_hostname", self.get_xml_element_value(
                    node, "dhcp-hostname")),
                ("dhcp_vendor", self.get_xml_element_value(
                    node, "dhcp-vendor")),

                ("seen-cards", self.get_seencards(node)),
            ))
        # wireless-client
        else:
            return OrderedDict((
                ("number", self.get_xml_attrib(node, "number", 0)),
                ("type", self.get_xml_attrib(node, "type", "unknown")),
                ("first_time", self.get_xml_attrib(node, "first-time")),
                ("last_time", self.get_xml_attrib(node, "last-time")),
                ("client_mac", self.get_xml_element_value(
                    node, "client-mac")),
                ("client_manuf", self.get_xml_element_value(
                    node, "client-manuf")),
                ("ssids", self.get_client_ssids(node)),
                ("channel", self.get_xml_element_value(
                    node, "channel", 0)),
                ("freqmhz", self.get_freqmhz(node)),
                ("maxseenrate", self.get_xml_element_value(
                    node, "maxseenrate", .0)),

                ("carrier", self.get_xml_values(node, "carrier")),
                ("encoding", self.get_xml_values(node, "encoding")),

                ("packets", self.get_packets(node)),
                ("datasize", self.get_xml_element_value(
                    node, "datasize", 0)),

                ("snr_info", self.get_snr(node)),
                ("gps_info", self.get_gpsinfo(node)),
                ("ip_address", self.get_ipaddress(node)),

                ("cdp_device", self.get_xml_element_value(
                    node, "cdp-device")),
                ("cdp_portid", self.get_xml_element_value(
                    node, "cdp-portid")),

                ("dhcp_hostname", self.get_xml_element_value(
                    node, "dhcp-hostname")),
                ("dhcp_vendor", self.get_xml_element_value(
                    node, "dhcp-vendor")),

                ("seencards", self.get_seencards(node)),

                #todo
                ("tag", [])
            ))

    """Parse all networks"""
    def get_networks(self):
        for net in self._netxml.findall("wireless-network"):
            network_json = self.get_network(net, False)

            clients = []

            # wireless-client
            for client in net.findall("wireless-client"):
                client_json = self.get_network(client, True)

                clients.append(client_json)

            network_json["wireless_client"] = clients

            yield network_json

if __name__ == "main":
    pass
