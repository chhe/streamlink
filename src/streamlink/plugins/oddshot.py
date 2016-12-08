# coding=utf-8
import re

from streamlink.plugin import Plugin
from streamlink.plugin.api import http, validate
from streamlink.plugin.api.utils import parse_json
from streamlink.exceptions import PluginError
from streamlink.stream import HTTPStream

QUALITY_WEIGHTS = {
    "source": 1080,
    "720p": 720,
    "480p": 480,
    "240p": 240
}

_url_re = re.compile(r"""
    http(s)?://oddshot.tv/s/(?P<shot_id>[\w\d\_]+)
""", re.VERBOSE)

_json_re = re.compile(r"""
    (.*<script id=\"preloaded-data\" type=\"application/json\">)(?P<json>\[.*\])(</script>.*)
""", re.M | re.DOTALL)

class Oddshot(Plugin):

    @classmethod
    def stream_weight(cls, key):
        weight = QUALITY_WEIGHTS.get(key)
        if weight:
            return weight, "oddshot"

        return Plugin.stream_weight(key)

    @classmethod
    def can_handle_url(cls, url):
        return _url_re.match(url)

    def __init__(self, url):
        Plugin.__init__(self, url)
        self.url = url

    def _get_quality_options(self):
        res = http.get(self.url)
        match = _json_re.search(res.text)
        if not match:
            raise PluginError("JSON not found in HTML")
        json = match.groupdict().get("json")
        json = parse_json(json)
        viewer_key = ""
        for key in json[1]["response"]["viewer"].keys():
            if key != "id":
                viewer_key = key
        return json[1]["response"]["viewer"][viewer_key]["renditions"]

    def _get_streams(self):
        quality_options = self._get_quality_options()
        streams = {}
        for quality_option in quality_options:
            stream = HTTPStream(self.session, quality_option["url"])
            streams[quality_option["type"]] = stream
        return streams

__plugin__ = Oddshot
