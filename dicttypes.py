from base64 import b64encode
from hashlib import md5
import logging
from pathlib import Path

import mutagen

logger = logging.getLogger(__name__)


class AudioFile(dict):

    fp = None

    def __init__(self, fp):
        super().__init__()
        self.fp = mutagen.File(fp)
        self['title'] = tagchooser(self.fp, 'TIT2', '©nam', 'TITLE')
        self['artist'] = tagchooser(self.fp, 'TPE1', '©ART', 'ARTIST')
        self['album'] = tagchooser(self.fp, 'TALB', '©alb', 'ALBUM')
        self['albumartist'] = tagchooser(self.fp, 'TPE2', 'aART', 'ALBUMARTIST')
        self['id'] = md5('{}{}{}'.format(self['title'], self['artist'], self['album']).encode()).hexdigest()
        self['spotifyid'] = 'NIL'
        self['whitelist'] = True


class Playlist(dict):

    def __init__(self, link):
        super().__init__()
        self['name'] = str(Path(link).stem)
        self['spotifyname'] = self['name']
        self['spotifyid'] = 'NIL'
        self['spotifypicture'] = 'artwork/{}.jpg'.format(self['name'])

    def get_name(self):
        return self['name']

    def get_spotifyname(self):
        return self['spotifyname']

    def get_spotifyid(self):
        return self['spotifyid']

    def get_spotifyname_id(self):
        return '{} - {}'.format(self.get_spotifyname(), self.get_spotifyid())

    def get_artwork(self):

        max_filesize = 190 * 1024

        pathobj = Path(self['spotifypicture'])
        if pathobj.is_file() and pathobj.stat().st_size <= max_filesize:
            with open(pathobj, 'rb') as fp:
                return b64encode(fp.read())

        logger.warning('Playlist ({}) [{}]: artwork fetching failed'.format('Local', self.get_name()))
        return None

    def set_spotifyname(self, name):
        self['spotifyname'] = name

    def set_spotifyid(self, spid):
        self['spotifyid'] = spid

    def set_spotifypicture(self, spic):
        self['spotifypicture'] = spic

    def set_spotifydetails(self, name, spid, spic):
        self.set_spotifyname(name)
        self.set_spotifyid(spid)
        self.set_spotifypicture(spic)


def tagchooser(audiofile, *args):

    value = None

    for val in args:
        try:
            if audiofile.get(val) is not None:
                value = audiofile.get(val)[0]
                break
        except ValueError:
            pass

    return value
