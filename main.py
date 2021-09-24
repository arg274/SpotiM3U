import argparse
import glob
import logging
import sys

from local_playlist_manager import playlists_db, playlist_csv_manager, local_trackids_dupeexists
from spotify_playlist_manager import process_playlist


def playlist_iter(plpath, replacement_tuple=('', ''), cacheflag=False, force_update=False, update_art=False,
                  regex_flag=False):

    logger = logging.getLogger(__name__)

    ext = '/**/*.m3u?*'

    if '.m3u' not in plpath:
        plpath = plpath + ext

    playlists = glob.glob(plpath, recursive=True)

    playlists_db(playlists)

    for playlist in playlists:

        if cacheflag:
            logger.debug('SpotiM3U ({}): Cache-only mode is enabled'.format('Pref'))

        playlist_df = playlist_csv_manager(playlist, replacement_tuple,
                                           force_update=force_update, regex_flag=regex_flag)
        dupeflag = local_trackids_dupeexists(playlist_df)

        if dupeflag:
            logger.warning('Playlist ({}): Dupe track IDs detected in {}, processing skipped'.format('Local', playlist))

        if not cacheflag and not dupeflag:
            process_playlist(playlist_df, playlist, update_art=update_art)


def logging_initiate(loglevel='info'):

    level_dict = {
        'info': logging.INFO,
        'debug': logging.DEBUG,
        'trace': logging.DEBUG,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'critical': logging.CRITICAL,
        'error': logging.ERROR
    }

    logger = logging.getLogger(__name__)
    logfilehandler = logging.FileHandler('spotim3u.log', encoding='utf-8')
    logconsolehandler = logging.StreamHandler(sys.stdout)
    logformat = u'%(asctime)s %(name)-10s %(levelname)-8s %(message)s'

    try:
        loglevel = level_dict.get(loglevel.lower())
        # noinspection PyArgumentList
        logging.basicConfig(handlers=[logfilehandler, logconsolehandler], level=loglevel, format=logformat)
    except (KeyError, ValueError, TypeError):
        # noinspection PyArgumentList
        logging.basicConfig(handlers=[logfilehandler, logconsolehandler], level=logging.INFO, format=logformat)
        logger.warning('SpotiM3U ({}): Invalid log level, defaulted to \'INFO\''.format('Pref'))


def main():

    parser = argparse.ArgumentParser(description='Sync Spotify playlists to local M3U/M3U8 playlists.')
    parser.add_argument('playlist_folder', type=str, help='Directory containing all the M3U/M38 files.')
    parser.add_argument('--cacheonly', action='store_true', help='Cache the results without updating Spotify.')
    parser.add_argument('--forceupdate', action='store_true', help='Force query tracks that are not available.')
    parser.add_argument('--updateart', action='store_true', help='Update artwork in the playlists.')
    parser.add_argument('--replacefrom', type=str, help='Text to be replaced in the playlists.')
    parser.add_argument('--replaceto', type=str, help='Replacement text for the playlists.')
    parser.add_argument('--loglevel', type=str, default='info', help='Set the logging level.')
    parser.add_argument('--regex', action='store_true', help='Use regex matching for replace.')
    args = parser.parse_args()

    args.replacefrom = args.replacefrom if args.replacefrom is not None else ''
    args.replaceto = args.replaceto if (args.replaceto is not None and args.replacefrom != '') else ''

    logging_initiate(args.loglevel)
    playlist_iter(args.playlist_folder, replacement_tuple=(args.replacefrom, args.replaceto), cacheflag=args.cacheonly,
                  force_update=args.forceupdate, update_art=args.updateart, regex_flag=args.regex)


if __name__ == '__main__':
    main()
