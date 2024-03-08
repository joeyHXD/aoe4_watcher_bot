import datetime
import random
from DOTA2_dicts import WIN_POSTIVE, WIN_NEGATIVE, LOSE_POSTIVE, LOSE_NEGATIVE
from api_access import get_item_info

building_info, upgrade_info, unit_info = get_item_info()

class gameData:
    def __init__(self, data):
        self.data = data
        self.game_id = data['gameId']
        self.game_mode = data['leaderboard'] # rm_2v2
        self.win_reason = data['winReason']
        self.map = data['mapName']
        self.duration = str(datetime.timedelta(seconds=data['duration']))
        # Convert Unix timestamps to datetime objects
        self.started_at = datetime.datetime.utcfromtimestamp(data['startedAt']).strftime('%Y-%m-%d %H:%M:%S')
        self.started_at = datetime.datetime.utcfromtimestamp(data['finishedAt']).strftime('%Y-%m-%d %H:%M:%S')
        self.players = data['players']

    def get_player(self, i):
        player = self.players[i]
        profile_id = player.get("profileId")
        result = player.get("result")
        total_cost_by_age = self.get_production_cost_by_age(player)
        for age in total_cost_by_age:
            total_cost_by_age[age] = total_cost_by_age[age]["total"]
        # print(total_cost_by_age)
        team = player.get("team")
        kills = player.get("_stats").get("kills")
        # print(f"team: {team} kills: {kills}")
        return profile_id, result, total_cost_by_age, team, kills
    
    def get_age_timing(self, player):
        """ Returns the highest age reached by any player in the game"""
        feudal = player["actions"].get("feudalAge")
        castle = player["actions"].get("castleAge")
        imperial = player["actions"].get("imperialAge")
        if feudal:
            feudal = feudal[0]
        if castle:
            castle = castle[0]
        if imperial:
            imperial = imperial[0]
        return feudal, castle, imperial
    
    def get_highest_age(self, player):
        feudal, castle, imperial = self.get_age_timing(player)
        if imperial:
            return "imperial"
        if castle:
            return "castle"
        if feudal:
            return "feudal"
        return "dark"
    
    def get_build_order(self, player):
        return player["buildOrder"]

    def get_production_cost_by_age(self, player):
        """ Returns the total cost of all units produced by age"""
        feudal, castle, imperial = self.get_age_timing(player)
        build_order = self.get_build_order(player)
        total_cost_by_age = {}
        for item in build_order:
            pbgid = item.get("pbgid")
            item_type = item.get("type") # Unit, Building, Technology, Upgrade
            if item_type == "Animal" or item_type == "Age":
                # sheep
                continue
            item_finished = item.get("finished")
            item_info = self.get_item_info(item_type, pbgid)
            if not item_info:
                print(f"unknown item id: {pbgid} type: {item_type}")
                continue
            item_cost_by_age = self.get_single_item_cost_by_age(item_finished, item_info, feudal, castle, imperial)
            # add the item's cost to the total cost of all items produced by age
            for age, cost in item_cost_by_age.items():
                if age in total_cost_by_age:
                    for resource_type in cost:
                        total_cost_by_age[age][resource_type] += cost[resource_type]
                else:
                    total_cost_by_age[age] = cost
        return total_cost_by_age

    def get_number_of_items_by_age(self, item_finished, feudal, castle, imperial):
        """ Returns the number of items produced by age"""
        count = {}
        for finished_time in item_finished:
            if finished_time == 0:
                if "free" not in count:
                    count["free"] = 0
                count["free"] += 1
                continue
            if imperial and finished_time > imperial:
                if "imperial" not in count:
                    count["imperial"] = 0
                count["imperial"] += 1
                continue
            if castle and finished_time > castle:
                if "castle" not in count:
                    count["castle"] = 0
                count["castle"] += 1
                continue
            if feudal and finished_time > feudal:
                if "feudal" not in count:
                    count["feudal"] = 0
                count["feudal"] += 1
                continue
            if "dark" not in count:
                count["dark"] = 0
            count["dark"] += 1
        return count

    def get_single_item_cost_by_age(self, item_finished, item_info, feudal, castle, imperial):
        """ Returns the total cost of a single item by age"""
        """e.g. A produced 150 villagers in imperial, each cost 50 meat, so 150 * 50 = 7500 meat"""
        item_cost = self.get_item_cost(item_info)
        count_by_age = self.get_number_of_items_by_age(item_finished, feudal, castle, imperial)
        total_cost_by_age = {}
        for age, count in count_by_age.items():
            if age == "free":
                # free means the item was produced at 0s, before the game started
                continue
            total_cost = self.create_cost_dict()
            for resource_type in total_cost: # key is meat, wood, gold, etc
                total_cost[resource_type] += count * item_cost[resource_type]
            total_cost_by_age[age] = total_cost
        return total_cost_by_age
    
    def get_item_info(self, type, pbgid):
        pbgid = str(pbgid)
        if type == "Unit":
            return unit_info.get(pbgid)
        if type == "Building":
            return building_info.get(pbgid)
        if type == "Upgrade":
            return upgrade_info.get(pbgid)
        
    def get_item_cost(self, item_info):
        return item_info.get("costs")

    def create_cost_dict(self):
        cost_dict = {
            "food": 0,
            "wood": 0,
            "stone": 0,
            "gold": 0,
            "vizier": 0,
            "oliveoil": 0,
            "total": 0,
        }
        return cost_dict
    
    def get_messages(self, player):
        profile_id = player.profile_id
        nickname = player.nickname
        messages = []
        my_kills = 0
        my_team = 0
        total_kills_my_team = 0
        total_kills_team0 = 0
        total_kills_team1 = 0
        for i in range(len(self.players)):
            player_profile_id, result, total_cost_by_age, team, kills = self.get_player(i)
            if total_cost_by_age["feudal"] > 6000:
                kills = kills * 1.2
            if player_profile_id == profile_id:
                my_kills = kills
                my_team = team
            if team == 0:
                total_kills_team0 += kills
            else:
                total_kills_team1 += kills
        if my_team == 0:
            total_kills_my_team = total_kills_team0
        else:
            total_kills_my_team = total_kills_team1
        # 检测击杀数是否达标
        positive = my_kills > total_kills_my_team * 2 / len(self.players) and result == "win"
        # 检测是否胜利
        win = result == "win"
        if win and positive:
            message_base = WIN_POSTIVE
        elif win and not positive:
            message_base = WIN_NEGATIVE
        elif not win and positive:
            message_base = LOSE_POSTIVE
        else:
            message_base = LOSE_NEGATIVE
        print_str += random.choice(message_base).format(nickname) + '\n'
        print_str += f"开始时间: {self.started_at}\n"
        print_str += f"持续时间: {self.duration}\n"
        print_str += f"游戏模式: [{self.game_mode}]\n"
        return messages