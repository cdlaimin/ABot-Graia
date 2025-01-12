from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.message.element import Source
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from util.sendMessage import safeSendGroupMessage
from util.TextModeration import text_moderation_async
from util.control import Permission, Interval, Rest, Function

from .beast import encode, decode


saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {"head": FullMatch("/嗷"), "anything": WildcardMatch(optional=True)}
            )
        ],
        decorators=[
            Function.require("Beast"),
            Permission.require(),
            Rest.rest_control(),
            Interval.require(),
        ],
    )
)
async def main_encode(group: Group, anything: WildcardMatch, source: Source):
    if anything.matched:
        try:
            msg = encode(anything.result.asDisplay())
            if (len(msg)) < 500:
                await safeSendGroupMessage(
                    group, MessageChain.create(msg), quote=source.id
                )
            else:
                await safeSendGroupMessage(
                    group, MessageChain.create("文字过长"), quote=source.id
                )
        except Exception:
            await safeSendGroupMessage(
                group, MessageChain.create("明文错误``"), quote=source.id
            )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {"head": FullMatch("/呜"), "anything": WildcardMatch(optional=True)}
            )
        ],
        decorators=[
            Function.require("Beast"),
            Permission.require(),
            Rest.rest_control(),
            Interval.require(),
        ],
    )
)
async def main_decode(group: Group, anything: WildcardMatch, source: Source):
    if anything.matched:
        try:
            msg = decode(anything.result.asDisplay())
            res = await text_moderation_async(msg)
            if res["status"]:
                await safeSendGroupMessage(
                    group, MessageChain.create(msg), quote=source.id
                )
        except Exception:
            await safeSendGroupMessage(
                group, MessageChain.create("密文错误``"), quote=source.id
            )
