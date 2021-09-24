import logging

import spotipy

from local_playlist_manager import get_playlist, get_local_trackids
from spotify_query_manager import set_auth

logger = logging.getLogger(__name__)


def get_spotify_playlist(sp_obj, playlist_obj):

    offset = 0
    playlist_id = playlist_obj['spotifyid']

    spotify_item_dicts = [sp_obj.playlist_items(playlist_id)]
    total_tracks = spotify_item_dicts[0]['total']

    while total_tracks > 100:
        logger.debug('Playlist ({}) [{}]: Pagination ongoing'.format('Spotify', playlist_obj.get_spotifyname_id()))
        offset = offset + 100
        total_tracks = total_tracks - 100
        spotify_item_dicts.append(sp_obj.playlist_items(playlist_id, offset=offset))

    return spotify_item_dicts


def get_spotify_playlist_trackids(sp_obj, playlist_obj):

    trackids = []

    pages = get_spotify_playlist(sp_obj, playlist_obj)

    logger.debug('Playlist ({}) [{}]: Getting the track IDs'.format('Spotify', playlist_obj.get_spotifyname_id()))
    for page in pages:
        items = page['items']
        for item in items:
            track = item['track']
            trackid = track['id']
            trackids.append(trackid)

    return trackids


def prune_playlist(playlist_obj, sp_obj, local_trackids, sp_trackids):

    playlist_id = playlist_obj.get_spotifyid()
    prune_trackids = [x for x in sp_trackids if x not in local_trackids]

    total_prunes = len(prune_trackids)

    if prune_trackids:

        offset = 0
        length = 100

        while total_prunes > 0:
            logger.debug('Playlist ({}) [{}]: Pruning playlist'.format('Spotify', playlist_obj.get_spotifyname_id()))
            sp_obj.playlist_remove_all_occurrences_of_items(playlist_id, items=prune_trackids[offset:offset + length])
            total_prunes = total_prunes - 100
            offset = offset + 100

        logger.info('Playlist ({}) [{}]: Pruned playlist'.format('Spotify', playlist_obj.get_spotifyname_id()))


def add_to_playlist(playlist_obj, sp_obj, local_trackids, sp_trackids):

    playlist_id = playlist_obj.get_spotifyid()
    add_trackids = [x for x in local_trackids if x not in sp_trackids]

    total_additions = len(add_trackids)

    if add_trackids:

        offset = 0
        length = 100

        while total_additions > 0:
            logger.debug('Playlist ({}) [{}]: Adding tracks to playlist'.format('Spotify',
                                                                                playlist_obj.get_spotifyname_id()))
            sp_obj.playlist_add_items(playlist_id, items=add_trackids[offset:offset + length])
            total_additions = total_additions - 100
            offset = offset + 100

        logger.info('Playlist ({}) [{}]: Added tracks to playlist'.format('Spotify', playlist_obj.get_spotifyname_id()))


def reorder_playlist(playlist_obj, sp_obj, local_trackids):

    playlist_id = playlist_obj.get_spotifyid()
    local_idx = 0
    reorder_flag = False
    sp_trackids = get_spotify_playlist_trackids(sp_obj, playlist_obj)

    if len(sp_trackids) != len(local_trackids):
        logger.error('Playlist ({}) [{}]: Track number mismatch,'
                     'reordering failed'.format('Spotify', playlist_obj.get_spotifyname_id()))
        return
    elif set(sp_trackids) != set(local_trackids):
        logger.error('Playlist ({}) [{}]: Tracks mismatch,'
                     'reordering failed'.format('Spotify', playlist_obj.get_spotifyname_id()))
        return

    for local_trackid in local_trackids:
        sp_idx = sp_trackids.index(local_trackid)
        if local_idx != sp_idx:
            reorder_flag = True
            sp_obj.playlist_reorder_items(playlist_id, range_start=sp_idx, insert_before=local_idx)
            sp_trackids = get_spotify_playlist_trackids(sp_obj, playlist_obj)
        local_idx = local_idx + 1

    if reorder_flag:
        logger.info('Playlist ({}) [{}]: Reordered playlist'.format('Spotify', playlist_obj.get_spotifyname_id()))


def update_playlist_artwork(playlist_obj, sp_obj):

    playlist_id = playlist_obj.get_spotifyid()
    playlist_art = playlist_obj.get_artwork()

    if playlist_art is not None:
        sp_obj.playlist_upload_cover_image(playlist_id, playlist_art)
        logger.info('Playlist ({}) [{}]: Updated artwork'.format('Spotify', playlist_obj.get_spotifyname_id()))


def process_playlist(df, playlist_link, update_art=False):

    current_playlist = get_playlist(playlist_link)

    auth_manager = set_auth(clientflag=True)
    sp = spotipy.Spotify(client_credentials_manager=auth_manager)

    if current_playlist['spotifyid'] != 'NIL':
        sp_trackids = get_spotify_playlist_trackids(sp, current_playlist)
        local_trackids = get_local_trackids(df)

        logger.info('Playlist ({}) [{}]: Started processing'.format('Spotify', current_playlist.get_spotifyname_id()))

        prune_playlist(current_playlist, sp, local_trackids, sp_trackids)
        add_to_playlist(current_playlist, sp, local_trackids, sp_trackids)
        reorder_playlist(current_playlist, sp, local_trackids)

        if update_art:
            logger.debug('SpotiM3U ({}): Update artwork is enabled'.format('Pref'))
            update_playlist_artwork(current_playlist, sp)

        logger.info('Playlist ({}) [{}]: Finished processing'.format('Spotify', current_playlist.get_spotifyname_id()))
