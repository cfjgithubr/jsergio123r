"""
    Plugin for ResolveURL
    Copyright (C) 2016 gujal

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import re
import json
from resolveurl import common
from resolveurl.plugins.lib import helpers
from resolveurl.resolver import ResolveUrl, ResolverError


class PornHubResolver(ResolveUrl):
    name = 'pornhub'
    domains = ['pornhub.com']
    pattern = r'(?://|\.)(pornhub\.com)/(?:view_video\.php\?viewkey=|embed/)([a-zA-Z0-9]+)'

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.RAND_UA}
        html = self.net.http_GET(web_url, headers=headers).content
        fvars = re.search(r"flashvars(?!')[^{]+([^;]+)", html)
        if fvars:
            sources = json.loads(fvars.group(1)).get('mediaDefinitions', [])
            sources = [(item.get("quality"), item.get("videoUrl")) for item in sources if item.get('format') != "hls" and item.get("videoUrl") != ""]
            if sources:
                return helpers.pick_source(helpers.sort_sources_list(sources)) + helpers.append_headers(headers)

        vars = re.findall(r'var\s+(.+?)\s*=\s*(.+?);', html)
        links = re.findall(r'quality_(\d+)p\s*=\s*(.+?);', html)
        if links:
            sources = []
            for source in links:
                link = [i.strip() for i in source[1].split('+')]
                link = [i for i in link if i.startswith('*/')]
                link = [re.sub(r'^\*/', '', i) for i in link]
                link = [(i, [x[1] for x in vars if x[0] == i]) for i in link]
                link = [i[1][0] if i[1] else i[0] for i in link]
                link = ''.join(link)
                link = re.sub(r'\s|\+|\'|\"', '', link)
                sources.append([source[0], link])
            if sources:
                return helpers.pick_source(helpers.sort_sources_list(sources)) + helpers.append_headers(headers)

        raise ResolverError('File not found')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://www.{host}/view_video.php?viewkey={media_id}')

    @classmethod
    def _is_enabled(cls):
        return True
