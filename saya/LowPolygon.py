import httpx
import asyncio
import triangler
import matplotlib.pyplot as plt

from io import BytesIO
from loguru import logger
from typing import Optional
from PIL import Image as IMG
from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Plain, At, Source, Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ArgumentMatch,
    WildcardMatch,
)

from database.db import reduce_gold
from util.sendMessage import safeSendGroupMessage
from config import yaml_data, group_data, COIN_NAME
from util.control import Permission, Interval, Rest


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

WAITING = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {
                    "head": FullMatch("低多边形"),
                    "args": ArgumentMatch(
                        "-P", action="store", regex="\\d+", optional=True
                    ),
                    "anythings1": WildcardMatch(optional=True),
                },
            )
        ],
        decorators=[Permission.require(), Rest.rest_control(), Interval.require()],
    )
)
async def low_poly(
    group: Group,
    member: Member,
    source: Source,
    args: ArgumentMatch,
    anythings1: WildcardMatch,
):

    if (
        yaml_data["Saya"]["LowPolygon"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "LowPolygon" in group_data[str(group.id)]["DisabledFunc"]:
        return

    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter1(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            elif waiter1_message.has(Image):
                return waiter1_message.getFirst(Image).url
            else:
                await safeSendGroupMessage(group, MessageChain.create([Plain("请发送图片")]))

    if member.id not in WAITING:
        WAITING.append(member.id)
        image_url = None
        point = None

        if args.matched:
            point = int(args.result)
            if 99 < point < 3001:
                point = point
            else:
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("-P ：请输入100-3000之间的整数")])
                )

        if anythings1.matched:
            if anythings1.result.has(Image):
                image_url = anythings1.result.getFirst(Image).url
            elif anythings1.result.has(At):
                atid = anythings1.result.getFirst(At).target
                image_url = f"http://q1.qlogo.cn/g?b=qq&nk={atid}&s=640"

        if not image_url:
            await safeSendGroupMessage(
                group, MessageChain.create([At(member.id), Plain(" 请发送图片以进行制作")])
            )
            try:
                image_url = await asyncio.wait_for(inc.wait(waiter1), timeout=30)
                if not image_url:
                    WAITING.remove(member.id)
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain("已取消")])
                    )
            except asyncio.TimeoutError:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("等待超时")]), quote=source.id
                )

        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url)
            if resp.status_code != 200:
                return await safeSendGroupMessage(
                    group,
                    MessageChain.create([Plain(f"图片错误 {resp.status_code}")]),
                )
            img_bytes = resp.content
        if not await reduce_gold(str(member.id), 1):
            WAITING.remove(member.id)
            return safeSendGroupMessage(group, MessageChain.create(f"你的{COIN_NAME}不足"))
        await safeSendGroupMessage(
            group, MessageChain.create([Plain(f"正在生成{point if point else '默认'}切面，请稍后")])
        )
        image = await asyncio.to_thread(make_low_poly, img_bytes, point)
        if image:
            await safeSendGroupMessage(
                group, MessageChain.create([Image(data_bytes=image)])
            )
        else:
            await safeSendGroupMessage(group, MessageChain.create([Plain("生成失败")]))
        WAITING.remove(member.id)


def make_low_poly(img_bytes, point: Optional[int] = None):
    try:
        img = IMG.open(BytesIO(img_bytes)).convert("RGB")
        img.thumbnail((1000, 1000))
        imgx, imgy = img.size
        t = triangler.Triangler(
            sample_method=triangler.SampleMethod.POISSON_DISK,
            points=point if point else max(imgx, imgy),
        )
        bio = BytesIO()
        img = plt.imsave(bio, t.convert(img.__array__()))
        img = IMG.open(bio).convert("RGB")
        bio = BytesIO()
        img.save(bio, "JPEG")
    except Exception as e:
        logger.error(e)
        return None

    return bio.getvalue()
