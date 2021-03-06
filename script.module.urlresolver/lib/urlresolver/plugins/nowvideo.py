"""
    urlresolver XBMC Addon
    Copyright (C) 2011 t0mm0

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re, urllib, urllib2, os
from t0mm0.common.net import Net
from urlresolver import common
from urlresolver.plugnplay.interfaces import UrlResolver
from urlresolver.plugnplay.interfaces import PluginSettings
from urlresolver.plugnplay import Plugin
from lib import unwise

#SET ERROR_LOGO# THANKS TO VOINAGE, BSTRDMKR, ELDORADO & RESOLVING BY MIKEY1234
error_logo = os.path.join(common.addon_path, 'resources', 'images', 'redx.png')

class NowvideoResolver(Plugin, UrlResolver, PluginSettings):
    implements = [UrlResolver, PluginSettings]
    name = "nowvideo"
    domains = [ "nowvideo.eu","nowvideo.ch","nowvideo.sx" ]

    def __init__(self):
        p = self.get_setting('priority') or 100
        self.priority = int(p)
        self.net = Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        try:
            html = self.net.http_GET(web_url).content
            key = re.compile('flashvars.filekey=(.+?);').findall(html)
            ip_key = key[0]
            pattern = 'var %s="(.+?)".+?flashvars.file="(.+?)"'% str(ip_key)
            r = re.search(pattern,html, re.DOTALL)
            if r:
                filekey, filename= r.groups()
            else:
                r = re.search('file no longer exists',html)
                if r:
                    raise Exception ('File Not Found or removed')
            
            #get stream url from api
            api = 'http://www.nowvideo.sx/api/player.api.php?key=%s&file=%s' % (filekey, filename)
            html = self.net.http_GET(api).content
            r = re.search('url=(.+?)&title', html)
            if r:
                stream_url = urllib.unquote(r.group(1))
            else:
                r = re.search('no longer exists',html)
                if r:
                    raise Exception ('File Not Found or removed')
                raise Exception ('Failed to parse url')
            
            try:
                # test the url, should throw 404
                nv_header = self.net.http_HEAD(stream_url)
            except urllib2.HTTPError, e:
                # if error 404, redirect it back (two pass authentification)
                api = 'http://www.nowvideo.sx/api/player.api.php?pass=undefined&cid3=undefined&key=%s&user=undefined&numOfErrors=1&errorUrl=%s&cid=1&file=%s&cid2=undefined&errorCode=404' % (filekey, urllib.quote_plus(stream_url), filename)
                html = self.net.http_GET(api).content
                r = re.search('url=(.+?)&title', html)
                if r:
                    stream_url = urllib.unquote(r.group(1))
                
            return stream_url
        except urllib2.HTTPError, e:
            common.addon.log_error('Nowvideo: got http error %d fetching %s' %
                                    (e.code, web_url))
            return self.unresolvable(code=3, msg=e)
        except Exception, e:
            common.addon.log_error('**** Nowvideo Error occured: %s' % e)
            common.addon.show_small_popup(title='[B][COLOR white]NOWVIDEO[/COLOR][/B]', msg='[COLOR red]%s[/COLOR]' % e, delay=5000, image=error_logo)
            return self.unresolvable(code=0, msg=e)

    def get_url(self, host, media_id):
        return 'http://embed.nowvideo.sx/embed.php?v=%s' % media_id

    def get_host_and_id(self, url):
        r = re.search('((?:http://|www.|embed.)nowvideo.(?:eu|sx|ch))/(?:video/|embed.php\?.*?v=)([0-9a-z]+)', url)
        if r:
            return r.groups()
        else:
            return False

    def valid_url(self, url, host):
        if self.get_setting('enabled') == 'false': return False
        return re.match('http://(www.|embed.)?nowvideo.(?:eu|sx|ch)/(video/|embed.php\?)(?:[0-9a-z]+|width)', url) or 'nowvideo' in host
