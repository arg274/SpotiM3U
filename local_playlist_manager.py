import logging
import os
from pathlib import Path

import pandas as pd

from dicttypes import AudioFile, Playlist
from spotify_query_manager import get_spotify_id_nullsafe

logger = logging.getLogger(__name__)


def get_playlist(playlist_link):

    current_playlist = Playlist(playlist_link)

    playlist_db = 'db/{}.csv'.format('playlist')
    playlist_df = pd.read_csv(playlist_db)

    logger.debug('Playlist ({}) [{}]: Querying local file from the database'.format('Local',
                                                                                    current_playlist.get_name()))
    for index, row in playlist_df.iterrows():
        if row['name'] == current_playlist['name']:
            current_playlist.set_spotifydetails(row['spotifyname'], row['spotifyid'], row['spotifypicture'])
            break

    return current_playlist


def get_local_trackids(df):
    logger.debug('Playlist ({}): Filtering playlist'.format('Local'))
    df = df.loc[(df['spotifyid'] != 'NOT_AVAIL') & (df['spotifyid'] != 'NIL') & (df['whitelist'])]
    return df['spotifyid'].tolist()


def local_trackids_dupeexists(df):
    logger.debug('Playlist ({}): Checking dupes'.format('Local'))
    trackids = get_local_trackids(df)

    return len(trackids) != len(set(trackids))


# noinspection PyTypeChecker
def playlist_csv_manager(playlist, replacepath, force_update=False):

    songs = []

    with open(playlist, 'r', encoding='utf-8') as fp:
        logger.debug('Playlist ({}): Reading file \'{}\''.format('Local', playlist))
        playlist_obj = get_playlist(playlist)
        files = fp.readlines()
        for file in files:
            cur_file = file.strip().replace(replacepath[0], replacepath[1])
            if os.path.isfile(cur_file):
                cur_audiofile = AudioFile(cur_file)
                songs.append(cur_audiofile)

    df = pd.DataFrame(songs).set_index('id')

    Path('db').mkdir(parents=True, exist_ok=True)
    playlist_db = 'db/{}.csv'.format(playlist_obj.get_spotifyname_id())

    if os.path.isfile(playlist_db):
        csv_df = pd.read_csv(playlist_db).set_index('id')
        df['spotifyid'] = csv_df['spotifyid']
        df['whitelist'] = csv_df['whitelist']
        df = csv_df.reset_index().merge(df.reset_index(), how='right').set_index('id')
        df['spotifyid'].fillna('NIL', inplace=True)
        df['whitelist'].fillna(True, inplace=True)

    logger.debug('Playlist ({}) [{}]: Started populating Spotify track IDs'.format('Local', Path(playlist).stem))
    df['spotifyid'] = df.apply(lambda row: get_spotify_id_nullsafe(
        row['title'], row['artist'], row['album'], row['spotifyid'], force_update=force_update), axis=1)

    logger.debug('Playlist ({}) [{}]: Writing CSV to \'{}\''.format('Local', playlist_obj.get_name(), playlist_db))
    df.to_csv(playlist_db, encoding='utf-8-sig')

    return df


def playlists_db(playlists):

    playlist_objs = [Playlist(x) for x in playlists]
    playlist_df = pd.DataFrame(playlist_objs).sort_values(by='name').reset_index(drop=True)

    Path('db').mkdir(parents=True, exist_ok=True)
    Path('artwork').mkdir(parents=True, exist_ok=True)
    playlist_db = 'db/{}.csv'.format('playlist')

    if not os.path.isfile(playlist_db):
        logger.debug('SpotiM3U ({}): Writing CSV to \'{}\''.format('DB', playlist_db))
        playlist_df.to_csv(playlist_db, encoding='utf-8-sig', index=False)
    else:
        logger.debug('SpotiM3U ({}): Updating CSV \'{}\''.format('DB', playlist_db))
        csv_df = pd.read_csv(playlist_db).sort_values(by='name').reset_index(drop=True)
        playlist_df = pd.concat([playlist_df, csv_df]).\
            drop_duplicates(subset='name', keep='last').sort_values(by='name').reset_index(drop=True)
        playlist_df.to_csv(playlist_db, encoding='utf-8-sig', index=False)
