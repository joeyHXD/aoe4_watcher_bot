from .api_access import check_player, get_last_match_id, get_game_info
from hoshino import Service, priv
from .text2img import image_draw
from .player import Player
import json
import os
from .game_data import gameData

sv = Service(
            'aoe4_watcher_bot',
            use_priv=priv.SUPERUSER,
            enable_on_default=False,
            manage_priv=priv.SUPERUSER,
            visible=True,
            help_='添加帝四玩家 [玩家昵称] [steam的id]\n如：添加帝四玩家 萧瑟先辈 898754153\n'
    )

proxies = {"http": "", "https": ""}

@sv.on_prefix('转换id')
async def steam_id_convert_32_to_64(bot, ev):
    s = ev.message.extract_plain_text()
    await bot.send(ev, str(int(s) + 76561197960265728)) 

bot = sv.bot
data = {}
player_info_path = os.path.join(os.path.dirname(__file__), "playerInfo.json")

with open(player_info_path, encoding="utf-8") as file:
    tmp = json.load(file)

for gid, player_list in tmp.items():
    data[gid] = []
    for info in player_list:
        player = Player()
        player.load_dict(info)
        data[gid].append(player)

def save_to_json():
    tmp = {}
    for gid, player_list in data.items():
        tmp[gid] = []
        for player in player_list:
            tmp[gid].append(player.to_dict())
    with open(player_info_path, "w", encoding="utf-8") as file:
        json.dump(tmp, file, indent=4, ensure_ascii=False)

@sv.scheduled_job('interval', seconds=60)
async def update():
    sv.logger.info("fetching AOE4 data")
    messages = ""
    for gid, player_list in data.items():
        for player in player_list:
            last_match_ID, updated_at = get_last_match_id(player.profile_id)
            if updated_at != player.updated_at and last_match_ID != player.last_match_ID:
                """
                更新时间updated_at永远会更新
                最后一场比赛ID last_match_ID只有成功获取到比赛数据时才会更新
                这里有四种情况
                1. 最后一场比赛ID和更新时间都不同，说明有新的比赛
                2. 最后一场比赛ID和更新时间都相同，说明没有新的比赛
                3. 最后一场比赛ID不同，但更新时间相同，说明有新的比赛，但是获取比赛数据失败
                4. 最后一场比赛ID相同，但更新时间不同，说明比赛数据已经获取过了，但是网站上的数据更新了，不需要再次获取
                所以，只有在情况1下才需要获取比赛数据
                """
                player.updated_at = updated_at
                try:
                    game_info = get_game_info(player.profile_id, last_match_ID)
                    game = gameData(game_info)
                    messages = game.get_messages(player)
                    player.last_match_ID = last_match_ID
                except:
                    sv.logger.info(f"获取{player.nickname}的游戏数据失败，可能是没有公开或正在进行中")
                break
    if messages:
        data[gid] = player_list
        sv.logger.info(messages)
        pic = image_draw(messages)
        try:
            await bot.send_group_msg(group_id=gid, message=f'[CQ:image,file={pic}]')
        except:
            sv.logger.info(f"临时会话图片发送失败")
            # await bot.send_group_msg(group_id=gid, message="图片发送失败")
        save_to_json()
    sv.logger.info("done")

@sv.on_prefix('添加帝四玩家')
async def add_aoe4_player(bot, ev):
    cmd = ev.raw_message
    content=cmd.split()
    if(len(content)!=3):
        reply="请输入：添加帝四玩家 [玩家昵称] [steam的id]\n如：添加帝四玩家 萧瑟先辈 898754153\n"
        await bot.finish(ev, reply)
    nickname = content[1]
    steam_id = content[2] # 可以是steam_id或者profile_id，甚至用户名
    player_name, profile_id = check_player(steam_id)
    if not profile_id:
        reply = f"未找到玩家{steam_id}"
        await bot.finish(ev, reply)
    gid = str(ev['group_id'])
    # 新建一个玩家对象, 放入玩家列表
    temp_player = Player(profile_id=profile_id,
                         nickname=nickname,
                         updated_at=0,
                         last_match_ID=0)
    if gid not in data:
        data[gid] = []
    for player in data[gid]:
        if player.profile_id == profile_id:
            player.nickname = nickname
            reply = "玩家已存在，更新昵称"
            break
    else:
        reply = "玩家添加成功"
        data[gid].append(temp_player)
    save_to_json()
    await bot.send(ev, reply)
    