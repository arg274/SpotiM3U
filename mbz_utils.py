import logging
import os
import yaml

import musicbrainzngs

logger = logging.getLogger(__name__)


def set_auth(config_file='config.yaml'):

    if os.path.isfile(config_file):
        with open(config_file, 'r') as fp:
            auth_dict = yaml.safe_load(fp)
            try:
                creds = auth_dict['mbz_creds']
                logger.debug('Auth ({}): Setting user-agent and rate-limit'.format('MBZ'))
                musicbrainzngs.set_useragent(app=creds['useragent']['app'],
                                             version=creds['useragent']['version'],
                                             contact=creds['useragent']['contact'])
                musicbrainzngs.set_rate_limit(limit_or_interval=float(creds['rate_limit']['limit_or_interval']),
                                              new_requests=int(creds['rate_limit']['new_requests']))
            except (TypeError, KeyError):
                logger.error('SpotiM3U ({}): Invalid YAML (MBZ)'.format('Func'))


def get_romanised_name(artist):

    set_auth()

    romanised_name = None
    logger.debug('Query ({}): Querying with \'{}\''.format('MBZ', artist))
    artist_search_result = musicbrainzngs.search_artists(artist=artist, limit=5)

    if artist_search_result['artist-count'] > 0:
        romanised_name = artist_search_result['artist-list'][0]['sort-name'].replace(',', '')

    return romanised_name
