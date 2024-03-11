import json
import requests
from logging import getLogger
from bs4 import BeautifulSoup

logger = getLogger(__name__)
session = requests.session()

request_header = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'}

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
            # steam_id = resp.get('steam_id')
            logger.info(
                f"Found player by profile_id: {player_name} ({profile_id})"
            )
            return player_name, profile_id
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
            # steam_id = resp['players'][0].get('steam_id')
            logger.info(
                f"Found player by query: {player_name} ({profile_id})"
            )
            return player_name, profile_id
    except Exception:
        logger.exception("")

    logger.info(f"Failed to find a player with: {text}")
    return None, None

def get_last_match_id(id):
    """ Gets match history and adds some data its missing"""
    url = f"https://aoe4world.com/api/v0/players/{id}/games/last?include_stats=true"
    try:
        resp = session.get(url).text
        data = json.loads(resp)
        return data["game_id"], data["updated_at"]
    except Exception:
        logger.exception("")
        return None

def get_game_info(profile_id, match_id):
    # URL of the website you want to crawl
    url = f'https://aoe4world.com/players/{profile_id}/games/{match_id}/summary?camelize=true'
    # Send a GET request to the URL
    response = requests.get(url, headers = request_header)
    result = []
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all tbody elements
        tbody_elements = soup.find_all('tbody')
        result.append(tbody_elements)
        # Print the found tbody elements
    else:
        print('Failed to retrieve the webpage.')
    return json.loads(response.text)

def get_item_info():
    url = "https://data.aoe4world.com/buildings/all.json"
    response = requests.get(url)
    building_data = response.json()
    building_info = {}
    for building in building_data["data"]:
        building_id = building["pbgid"]
        building_id = str(building_id)
        building_info[building_id] = building

    url = "https://data.aoe4world.com/upgrades/all.json"
    response = requests.get(url)
    upgrade_data = response.json()
    upgrade_info = {}
    for upgrade in upgrade_data["data"]:
        upgrade_id = upgrade["pbgid"]
        upgrade_id = str(upgrade_id)
        upgrade_info[upgrade_id] = upgrade

    url = "https://data.aoe4world.com/technologies/all.json"
    response = requests.get(url)
    technology_data = response.json()
    # technology_info = {}
    # technology is combined into upgrade_info
    for technology in technology_data["data"]:
        technology_id = technology["pbgid"]
        technology_id = str(technology_id)
        upgrade_info[technology_id] = technology

    url = "https://data.aoe4world.com/units/all.json"
    response = requests.get(url)
    unit_data = response.json()
    unit_info = {}
    for unit in unit_data["data"]:
        unit_id = unit["pbgid"]
        unit_id = str(unit_id)
        unit_info[unit_id] = unit

    return building_info, upgrade_info, unit_info