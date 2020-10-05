import logging
import os
import re
import sys

import spotipy
import yaml
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from mbz_utils import get_romanised_name

logger = logging.getLogger(__name__)


def set_auth(config_file='config.yaml', clientflag=False):

    if os.path.isfile(config_file):
        with open(config_file, 'r') as fp:
            auth_dict = yaml.safe_load(fp)
            try:
                client_id = auth_dict['spotify_creds']['client_id']
                client_secret = auth_dict['spotify_creds']['client_secret']
                redirect_uri = auth_dict['spotify_creds']['redirect_uri']

                if client_id == 'none' or client_secret == 'none':
                    logger.error(
                        'SpotiM3U ({}): Edit the config.yaml for SpotiM3U to work'.format('Func'))
                    sys.exit(1)

                if clientflag:
                    logger.debug('Auth ({}): Attempting client authorisation'.format('Spotify'))
                    scope = 'playlist-modify-public playlist-read-collaborative playlist-read-private ' \
                            'playlist-modify-private ugc-image-upload'
                    auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret,
                                                redirect_uri=redirect_uri, scope=scope)
                else:
                    logger.debug('Auth ({}): Attempting server-side authorisation'.format('Spotify'))
                    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)

                return auth_manager

            except (KeyError, TypeError):
                logger.error('SpotiM3U ({}): Invalid YAML (Spotify)'.format('Func'))

    else:
        logger.error('SpotiM3U ({}): Creating YAML; edit the config.yaml for SpotiM3U to work'.format('Func'))
        default_dict = {
            'spotify_creds': {
                'client_id': 'none',
                'client_secret': 'none',
                'redirect_uri': 'http://localhost/'
            },
            'mbz_creds': {
                'useragent': {
                    'app': 'MBZPyQuery',
                    'version': '0.1',
                    'contact': 'yourmailhere@domain.com'
                },
                'rate_limit': {
                    'limit_or_interval': 1.0,
                    'new_requests': 1
                }
            }
        }
        with open(config_file, 'w') as fp:
            yaml.safe_dump(default_dict, fp)
            sys.exit(1)

    return None


def get_spotify_id(title, artist, album):

    auth_manager = set_auth()
    title = '"' + re.sub(r'\([Ff]eat\.? .+\)', '', title).strip() + '"'

    if auth_manager is None:
        logger.error('SpotiM3U ({}): Authorisation failed'.format('Func'))
    else:
        sp = spotipy.Spotify(client_credentials_manager=auth_manager)
        query = 'track:{} album:{} artist:{}'.format(title, album, artist)
        logger.debug('Query ({}): Querying with \'{}\''.format('Spotify', query))
        result = sp.search(q=query, limit=1)

        try:
            return result['tracks']['items'][0]['id']
        except (KeyError, TypeError, IndexError):
            try:
                query = 'track:{} artist:{}'.format(title, get_romanised_name(artist))
                logger.debug('Query ({}): Querying (alt) with \'{}\''.format('Spotify', query))
                result = sp.search(q=query, limit=1)
                return result['tracks']['items'][0]['id']
            except (KeyError, TypeError, IndexError):
                logger.warning('Query ({}): Query not found \'{}\''.format('Spotify', query))
                return 'NOT_AVAIL'


def get_spotify_id_nullsafe(title, artist, album, nullflag, force_update=False):

    if nullflag == 'NIL':
        return get_spotify_id(title, artist, album)
    elif force_update is True and nullflag == 'NOT_AVAIL':
        logger.debug('SpotiM3U ({}): Force update is enabled'.format('Pref'))
        return get_spotify_id(title, artist, album)

    return nullflag
