import datetime
import random
from .AOE4_dicts import WIN_POSTIVE, WIN_NEGATIVE, LOSE_POSTIVE, LOSE_NEGATIVE, CIVILIZATION, AGE, REASON
from .api_access import get_item_info

building_info, upgrade_info, unit_info = get_item_info()

class gameData:
    villager_id = "11119068"
    gilded_villager_id = "11254058"
    town_center_id = "11119069"
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
        return player
    
    def get_player_profile_id(self, player):
        profile_id = player.get("profileId")
        if not profile_id:
            print("error: profile_id not found in gameData")
        return profile_id
    
    def get_player_result(self, player):
        result = player.get("result")
        return result
    
    def get_player_cost_by_age(self, player):
        total_cost_by_age = self.get_production_cost_by_age(player)
        for age in total_cost_by_age:
            total_cost_by_age[age] = total_cost_by_age[age]["total"]
        return total_cost_by_age
    
    def get_player_team(self, player):
        team = player.get("team")
        if team == None:
            print("error: team not found in gameData")
        return team
    
    def get_player_kills(self, player):
        kills = player.get("_stats").get("elitekill")
        if not kills:
            print("error: kills not found in gameData")
            kills = 0
        return kills
    
    def get_player_civilization(self, player):
        civilization = player.get("civilization")
        if not civilization:
            print("error: civilization not found in gameData")
        return civilization
    
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
    
    def get_specific_age_timing(self, player, age):
        """ Returns the time at which a specific age was reached by a player"""
        feudal, castle, imperial = self.get_age_timing(player)
        if age == "imperial":
            return imperial
        if age == "castle":
            return castle
        if age == "feudal":
            return feudal
        return 0

    def get_build_order(self, player):
        return player["buildOrder"]

    def get_villager_count(self, player):
        build_order = self.get_build_order(player)
        for item in build_order:
            if item.get("id") == self.villager_id or item.get("id") == self.gilded_villager_id:
                return len(item.get("finished"))

    def get_tc_count(self, player):
        build_order = self.get_build_order(player)
        count = 0
        for item in build_order:
            if item.get("id") == self.town_center_id:
                count += len(item.get("constructed"))
        return count

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
        # 因为不知道哪个是自己，所以需要遍历所有玩家
        my_player = None
        total_kills_team0 = 0
        total_kills_team1 = 0
        total_true_kills_team0 = 0
        total_true_kills_team1 = 0
        for i in range(len(self.players)):
            this_player = self.get_player(i)
            player_profile_id = self.get_player_profile_id(this_player)
            total_cost_by_age = self.get_player_cost_by_age(this_player)
            team = self.get_player_team(this_player)
            kills = self.get_player_kills(this_player)
            if team == 0:
                total_true_kills_team0 += kills
            else:
                total_true_kills_team1 += kills
            if total_cost_by_age["feudal"] > 6000:
                # 如果卷2本，击杀数加成20%
                kills = kills * 1.2
            if player_profile_id == profile_id:
                my_player = this_player
                my_balanced_kills = kills
            if team == 0:
                total_kills_team0 += kills
            else:
                total_kills_team1 += kills

        my_kills = self.get_player_kills(my_player)
        my_team = self.get_player_team(my_player)
        my_result = self.get_player_result(my_player)
        my_civilization = self.get_player_civilization(my_player)
        my_tc_count = self.get_tc_count(my_player)
        my_villager_count = self.get_villager_count(my_player)
        my_highest_age = self.get_highest_age(my_player)
        my_highest_age_timing = self.get_specific_age_timing(my_player, my_highest_age)
        my_highest_age_timing = str(datetime.timedelta(seconds=my_highest_age_timing))
        total_kills_my_team = 0
        total_true_kills_my_team = 0
        if my_team == 0:
            total_true_kills_my_team = total_true_kills_team0
            total_kills_my_team = total_kills_team0
        else:
            total_true_kills_my_team = total_true_kills_team1
            total_kills_my_team = total_kills_team1
        # 检测击杀数是否达标
        player_count_my_team = len(self.players) / 2
        my_kills_rate = my_kills / total_true_kills_my_team * 100
        positive = my_balanced_kills >= total_kills_my_team / player_count_my_team
        print(my_result)
        print(player_count_my_team)
        print(my_balanced_kills, total_kills_my_team)
        print(positive)
        # 检测是否胜利
        win = my_result == "win"
        if win and positive:
            message_base = WIN_POSTIVE
        elif win and not positive:
            message_base = WIN_NEGATIVE
        elif not win and positive:
            message_base = LOSE_POSTIVE
        else:
            message_base = LOSE_NEGATIVE
        print_str = random.choice(message_base).format(nickname) + '\n'
        print_str += f"开始时间: {self.started_at}\n"
        print_str += f"持续时间: {self.duration}\n"
        print_str += f"游戏模式: {self.game_mode}\n"
        print_str += f"地图: {self.map}\n"
        print_str += f"胜利条件: {REASON.get(self.win_reason, self.win_reason)}\n"
        print_str += f"所选文明: {CIVILIZATION.get(my_civilization, my_civilization)}\n"
        print_str += f"最高时代: {AGE[my_highest_age]}({my_highest_age_timing}),\n"
        print_str += f"农民数量: {my_villager_count},\n"
        print_str += f"总击杀: {my_kills}({my_kills_rate:.2f}%),\n"
        print_str += f"TC数量: {my_tc_count}\n"
        return print_str