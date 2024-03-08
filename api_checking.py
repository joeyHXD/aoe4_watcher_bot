import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from overlay.logging_func import get_logger

logger = get_logger(__name__)
session = requests.session()

def check_player(text: str) -> str:
    """ Tries to find a player based on a text containing either name, steam_id or profile_id
    Returns the player name and rank if found, otherwise returns None"""

    # First try if it's a profile id
    try:
        url = f"https://aoe4world.com/api/v0/players/{text}"
        resp = json.loads(session.get(url).text)
        if 'name' in resp:
            profile_id = resp['profile_id']
            player_name = resp['name']
            steam_id = resp.get('steam_id')
            logger.info(
                f"Found player by profile_id: {player_name} ({profile_id})"
            )
            return player_name, steam_id
    except json.decoder.JSONDecodeError:
        logger.error("Not a valid profile_id")
    except Exception:
        logger.exception("An unexpected error occurred when checking player: %s", e)

    # Then try query
    try:
        url = f"https://aoe4world.com/api/v0/players/search?query={text}"
        resp = json.loads(session.get(url).text)
        if resp['players']:
            profile_id = resp['players'][0]['profile_id']
            player_name = resp['players'][0]['name']
            steam_id = resp['players'][0].get('steam_id')
            logger.info(
                f"Found player by query: {player_name} ({profile_id})"
            )
            return player_name, steam_id
    except Exception:
        logger.exception("")

    logger.info(f"Failed to find a player with: {text}")
    return None, None


def get_full_match_history(amount: int) -> Optional[List[Any]]:
    """ Gets match history and adds some data its missing"""

    url = f"https://aoe4world.com/api/v0/players/{settings.profile_id}/games?limit={amount}"
    try:
        resp = session.get(url).text
        data = json.loads(resp)
        return data['games']
    except Exception:
        logger.exception("")
        return None


class Api_checker:

    def __init__(self):
        self.force_stop = False  # To stop the thread
        self.force_check = False  # This can force a check of new data
        self.last_match_timestamp = datetime(1900, 1, 1, 0, 0, 0)
        self.last_rating_timestamp = datetime(1900, 1, 1, 0, 0, 0)

    def reset(self):
        """ Resets last timestamps"""
        self.last_match_timestamp = datetime(1900, 1, 1, 0, 0, 0)
        self.last_rating_timestamp = datetime(1900, 1, 1, 0, 0, 0)
        self.force_check = True

    def sleep(self, seconds: int) -> bool:
        """ Sleeps while checking for force_stop
        Returns `True` if we need to stop the parent function"""
        for _ in range(seconds * 2):
            if self.force_stop:
                return True

            if self.force_check:
                self.force_check = False
                return False

            time.sleep(0.5)
        return False

    def check_for_new_game(self,
                           delayed_seconds: int = 0
                           ) -> Optional[Dict[str, Any]]:
        """ Continously check if there are a new game being played
        Returns match data if there is a new game"""

        if self.sleep(delayed_seconds):
            return

        while True:
            result = self.get_data()
            if result is not None:
                return result

            if self.sleep(settings.interval):
                return

    def get_data(self) -> Optional[Dict[str, Any]]:
        if self.force_stop:
            return

        # Get last match from aoe4world.com
        try:
            url = f"https://aoe4world.com/api/v0/players/{settings.profile_id}/games/last"
            resp = session.get(url)
            data = json.loads(resp.text)
        except Exception:
            logger.exception("")
            return

        if self.force_stop:
            return
        if "error" in data:
            return

        # Calc old leaderboard id
        data['leaderboard_id'] = 0
        try:
            data['leaderboard_id'] = int(data['kind'][-1]) + 16
        except Exception:
            logger.exception("")

        # Calc started time
        started = datetime.strptime(data['started_at'],
                                    "%Y-%m-%dT%H:%M:%S.000Z")
        data['started_sec'] = started.timestamp()

        # Show the last game
        if started > self.last_match_timestamp:  # and data['ongoing']:
            self.last_match_timestamp = started
            return data