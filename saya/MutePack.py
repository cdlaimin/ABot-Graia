import random

from time import strftime, gmtime
from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *
from graia.application.message.parser.literature import Literature

from config import sendmsg, group_data, yaml_data


saya = Saya.current()
channel = Channel.current()

if yaml_data['Saya']['MutePack']['MaxTime'] * yaml_data['Saya']['MutePack']['MaxMultiple'] * yaml_data['Saya']['MutePack']['MaxSuperDoubleMultiple'] > 2592000:
    print("禁言套餐最大基础时长设定超过30天，请检查配置文件")
    exit()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("我要禁言套餐")]))
async def random_mute(app: GraiaMiraiApplication, group: Group, member: Member):

    if yaml_data['Saya']['MutePack']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'MutePack' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    if member.id in yaml_data['Basic']['Permission']['Admin']:
        time = random.randint(60, 180)
    else:
        time = random.randint(60, yaml_data['Saya']['MutePack']['MaxTime'])
    multiple = random.randint(1, yaml_data['Saya']['MutePack']['MaxMultiple'])
    ftime = time * multiple
    srtftime = strftime("%H:%M:%S", gmtime(ftime))
    if random.randint(1, yaml_data['Saya']['MutePack']['MaxJackpotProbability']) == yaml_data['Saya']['MutePack']['MaxJackpotProbability']:
        try:
            await app.mute(group, member, 2592000)
            await app.sendGroupMessage(group, MessageChain.create([AtAll(), Plain(f"恭喜{member.name}中了头奖！获得30天禁言！")]))
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create(Plain(f"恭喜 {group.name} 群里的 {member.name} 中了禁言头奖")))
            quit()
        except PermissionError:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"权限不足，无法使用！\n使用该功能{yaml_data['Basic']['BotName']}需要为管理")]))
    elif yaml_data['Saya']['MutePack']['SuperDouble'] and random.randint(1, yaml_data['Saya']['MutePack']['MaxSuperDoubleProbability']) == yaml_data['Saya']['MutePack']['MaxSuperDoubleProbability']:
        try:
            ftime = ftime * \
                yaml_data['Saya']['MutePack']['MaxSuperDoubleMultiple']
            srtftime = strftime("%d:%H:%M:%S", gmtime(ftime))
            await app.mute(group, member, ftime)
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"恭喜你抽中了 {time} 秒禁言套餐！倍率为 {multiple}！\n超级加倍！\n最终时长为 {srtftime}")]))
        except PermissionError:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"权限不足，无法使用！\n使用该功能{yaml_data['Basic']['BotName']}需要为管理员权限或更高")]))
    else:
        try:
            await app.mute(group, member, ftime)
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"恭喜你抽中了 {time} 秒禁言套餐！倍率为 {multiple}\n最终时长为 {srtftime}")]))
        except PermissionError:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"权限不足，无法使用！\n使用该功能{yaml_data['Basic']['BotName']}需要为管理员权限或更高")]))