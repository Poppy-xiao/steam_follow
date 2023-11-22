import json
import os
from lxml import etree
from asyncio import sleep
from .draw import *
from hoshino import service, aiorequests
import aiofiles
from base64 import b64encode
import aiohttp
import traceback
import time
sv = service.Service("steam", enable_on_default=True)

current_folder = os.path.dirname(__file__)
config_file = os.path.join(current_folder, 'steam.json')
img_folder = os.path.join(current_folder, 'img') 
os.makedirs(img_folder, exist_ok=True)
with open(config_file, mode="r") as f:
    f = f.read()
    cfg = json.loads(f)

playing_state = {}
async def format_id(id:str)->str:
    if id.startswith('76') and len(id)==17:
        return id
    else:
        resp= await aiorequests.get(f'https://steamcommunity.com/id/{id}?xml=1')
        xml=etree.XML(await resp.content)
        return xml.xpath('/profile/steamID64')[0].text

@sv.on_prefix("添加steam订阅")
async def steam(bot, ev):
    account = str(ev.message).strip()
    try:
        await update_steam_ids(account, ev["group_id"])
        rsp = await get_account_status(account)
        if rsp["personaname"] == "":
            await bot.send(ev, "添加订阅失败！")
        cq_image_code = await create_and_send_player_status_image(rsp)
        await sv.bot.send(ev, message=cq_image_code + "\n订阅成功")

    except:
        print(traceback.format_exc())
        await bot.send(ev, "订阅失败")


@sv.on_prefix("取消steam订阅")
async def steam(bot, ev):
    account = str(ev.message).strip()
    try:
        await del_steam_ids(account, ev["group_id"])
        await bot.send(ev, "取消订阅成功")
    except:
        await bot.send(ev, "取消订阅失败")


@sv.on_prefix("steam订阅列表")
async def steam(bot, ev):
    group_id = ev["group_id"]
    await update_game_status()
    images = []

    for key, val in playing_state.items():
        if group_id in cfg["subscribes"].get(str(key), []):
            player_img = await create_player_status_image(val)
            images.append(player_img)

    if images:
        combined_img = concatenate_images_vertically(images)
        temp_file = os.path.join('/tmp', 'combined_status.png')
        combined_img.save(temp_file, 'PNG')

        async with aiofiles.open(temp_file, 'rb') as img_file:
            base64_str = b64encode(await img_file.read()).decode()
        cq_image_code = f'[CQ:image,file=base64://{base64_str}]'
        await bot.send(ev, cq_image_code)

        os.remove(temp_file)
    else:
        await bot.send(ev, "没有订阅的Steam玩家。")


@sv.on_prefix("查询steam账号")
async def steam(bot, ev):
    account = str(ev.message).strip()
    rsp = await get_account_status(account)
    if rsp["personaname"] == "":
        await bot.send(ev, "查询失败！")
    cq_image_code = await create_and_send_player_status_image(rsp)
    await sv.bot.send(ev, message=cq_image_code)

@sv.scheduled_job('cron', minute='*/1')
async def check_steam_status():
    old_state = playing_state.copy()
    play_time = None
    await update_game_status()
    if old_state == {}:
        return
    try:
        for key, val in playing_state.items():
            if val != old_state[key] :
                glist = set(cfg["subscribes"][key]) & set((await sv.get_enable_groups()).keys())
                for group in glist:
                    # 生成通知图片
                    avatar_path = os.path.join(img_folder, f'{key}.png')
                    avatar_url = val["avatarfull"]
                    await download_avatar_image(avatar_url, avatar_path)
                    if val["personastate"] == 0:
                        game_info = 'Offline'
                        status_text = ""
                    elif val["personastate"] == 1:
                        status_text = 'is now playing' if val["gameextrainfo"] else 'is not playing'
                        game_info = val["gameextrainfo"] if val["gameextrainfo"] else old_state.get(key, {}).get("gameextrainfo", "Online")
                        if old_state[key]["startTime"] and status_text == 'is not playing':
                            play_time = int(time.time()) - old_state[key]["startTime"]
                    
                    img = draw_rectangle_with_image_and_text(image_path=avatar_path, name=val["personaname"], game=game_info, status=status_text , play_time=play_time)
                    
                    temp_file = os.path.join('/tmp', f'{key}_status.png')
                    img.save(temp_file, 'PNG')

                    async with aiofiles.open(temp_file, 'rb') as img_file:
                        base64_str = b64encode(await img_file.read()).decode()
                    cq_image_code = f'[CQ:image,file=base64://{base64_str}]'
                    await sv.bot.send_group_msg(group_id=group, message=cq_image_code)
                    os.remove(avatar_path)
                    os.remove(temp_file)
                    await sleep(0.5)
    except:
        print(traceback.format_exc())

async def create_player_status_image(msg):
    key = msg["steamid"]
    avatar_path = os.path.join(img_folder, f'{key}.png')
    avatar_url = msg["avatarfull"]
    await download_avatar_image(avatar_url, avatar_path)
    if msg["personastate"] == 0:
        game_info = 'Offline'
        status_text = ""
        name = msg["personaname"]
    else:
        game_info = msg["gameextrainfo"] if msg["gameextrainfo"] else 'Online'
        status_text = 'is now playing' if msg["gameextrainfo"] else 'is not playing'
        name = msg["personaname"]
    return draw_rectangle_with_image_and_text(image_path=avatar_path, name=name, game=game_info, status=status_text)

async def create_and_send_player_status_image(msg,old_state=None):
    key = msg["steamid"]
    avatar_path = os.path.join(img_folder, f'{key}.png')
    avatar_url = msg["avatarfull"]
    await download_avatar_image(avatar_url, avatar_path)
    if msg["personastate"] == 0:
        game_info = 'Offline'
        status_text = ""
        name = msg["personaname"]
    else:
        game_info = msg["gameextrainfo"] if msg["gameextrainfo"] else 'Online'
        status_text = 'is now playing' if msg["gameextrainfo"] else 'is not playing'
        name = msg["personaname"]
    
    img = draw_rectangle_with_image_and_text(image_path=avatar_path, name=name, game=game_info, status=status_text)
    temp_file = os.path.join('/tmp', f'{key}_status.png')
    img.save(temp_file, 'PNG')
    async with aiofiles.open(temp_file, 'rb') as img_file:
        base64_str = b64encode(await img_file.read()).decode()
    cq_image_code = f'[CQ:image,file=base64://{base64_str}]'
    os.remove(temp_file)
    os.remove(avatar_path)
    return cq_image_code

async def download_avatar_image(avatar_url, path_to_save):
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as response:
            if response.status == 200:
                f = await aiofiles.open(path_to_save, mode='wb')
                await f.write(await response.read())
                await f.close()

async def get_account_status(id):
    id=await format_id(id)
    params = {
        "key": cfg["key"],
        "format": "json",
        "steamids": id
    }
    resp = await aiorequests.get("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/", params=params)
    rsp = await resp.json()
    friend = rsp["response"]["players"][0]
    return {
        "personaname": friend["personaname"] if "personaname" in friend else "",
        "gameextrainfo": friend["gameextrainfo"] if "gameextrainfo" in friend else "",
        "avatarfull": friend["avatarfull"],
        "steamid":friend["steamid"],
        "personastate" : friend["personastate"] if friend["personastate"] else 0,
        "startTime": None,
    }


async def update_game_status():
    params = {
        "key": cfg["key"],
        "format": "json",
        "steamids": ",".join(cfg["subscribes"].keys())
    }
    resp = await aiorequests.get("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/", params=params)
    rsp = await resp.json()

    for friend in rsp["response"]["players"]:
        steamid = friend["steamid"]
        personaname = friend.get("personaname", "")
        gameextrainfo = friend.get("gameextrainfo", "")
        avatarfull = friend["avatarfull"]
        personastate = friend["personastate"] if friend["personastate"] else 0,

        # 检查是否需要更新startTime
        current_start_time = playing_state.get(steamid, {}).get("startTime")
        if current_start_time is None and gameextrainfo and playing_state.get(steamid, {}).get("gameextrainfo", "") == "":
            new_start_time = int(time.time())
        elif personastate == 0:
            new_start_time = None
        else:
            new_start_time = current_start_time

        # 更新playing_state
        playing_state[steamid] = {
            "personaname": personaname,
            "gameextrainfo": gameextrainfo,
            "avatarfull": avatarfull,
            "steamid": steamid,
            "personastate": personastate,
            "startTime": new_start_time
        }



async def update_steam_ids(steam_id, group):
    steam_id=await format_id(steam_id)
    if steam_id not in cfg["subscribes"]:
        cfg["subscribes"][str(steam_id)] = []
    if group not in cfg["subscribes"][str(steam_id)]:
        cfg["subscribes"][str(steam_id)].append(group)
    with open(config_file, mode="w") as fil:
        json.dump(cfg, fil, indent=4, ensure_ascii=False)
    await update_game_status()


async def del_steam_ids(steam_id, group):
    steam_id=await format_id(steam_id)
    if group in cfg["subscribes"][str(steam_id)]:
        cfg["subscribes"][str(steam_id)].remove(group)
    with open(config_file, mode="w") as fil:
        json.dump(cfg, fil, indent=4, ensure_ascii=False)
    await update_game_status()


async def broadcast(group_list: set, msg):
    for group in group_list:
        await sv.bot.send_group_msg(group_id=group, message=msg)
        await sleep(0.5)
