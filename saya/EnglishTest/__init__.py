import asyncio

from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt import InterruptControl
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import Image_UnsafeBytes, MessageChain, Plain

from util.text2image import create_image

from .database.database import random_word


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


bookid = {
    "CET4luan_1": {"name": "四级真题核心词", "id": "1"},
    "CET6luan_1": {"name": "六级真题核心词", "id": "2"},
    "KaoYanluan_1": {"name": "考研必考词汇", "id": "3"},
    "Level4luan_1": {"name": "专四真题高频词", "id": "4"},
    "Level8_1": {"name": "专八真题高频词", "id": "5"},
    "IELTSluan_2": {"name": "雅思词汇", "id": "6"},
    "TOEFL_2": {"name": "TOEFL 词汇", "id": "7"},
    "ChuZhongluan_2": {"name": "中考必备词汇", "id": "8"},
    "GaoZhongluan_2": {"name": "高考必备词汇", "id": "9"},
    "PEPXiaoXue3_1": {"name": "人教版小学英语-三年级上册", "id": "10"},
    "PEPChuZhong7_1": {"name": "人教版初中英语-七年级上册", "id": "11"},
    "PEPGaoZhong": {"name": "人教版高中英语-必修", "id": "12"},
    "ChuZhong_2": {"name": "初中英语词汇", "id": "13"},
    "GaoZhong_2": {"name": "高中英语词汇", "id": "14"},
    "BEC_2": {"name": "商务英语词汇", "id": "15"},
}

booklist = []
for book in bookid:
    booklist.append(f"{bookid[book]['id']}. {bookid[book]['name']}")


Process = [1, 2, 3, 4]

RUNNING = {}


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("背单词")]))
async def learn(app: GraiaMiraiApplication, group: Group, member: Member):

    @Waiter.create_using_function([GroupMessage])
    async def confirm(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain):
        if all([waiter_group.id == group.id, waiter_member.id == member.id]):
            waiter_saying = waiter_message.asDisplay()
            if waiter_saying == "取消":
                return False
            else:
                try:
                    bookid = int(waiter_saying)
                    if 1 <= bookid <= 15:
                        return bookid
                except:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain("请输入1-15以内的数字")
                    ]))

    @Waiter.create_using_function([GroupMessage])
    async def waiter(waiter_group: Group, waiter_message: MessageChain):
        if waiter_group.id == group.id:
            waiter_saying = waiter_message.asDisplay()
            if waiter_saying == "取消":
                return False
            elif waiter_saying == RUNNING[group.id]:
                return True

    if group.id in RUNNING:
        return

    RUNNING[group.id] = None
    bookid_image = await create_image("\n".join(booklist))
    await app.sendGroupMessage(group, MessageChain.create([
        Plain("请输入你想要选择的词库ID"),
        Image_UnsafeBytes(bookid_image.getvalue())
    ]))

    try:
        bookid = await asyncio.wait_for(inc.wait(confirm), timeout=30)
        if not bookid:
            del RUNNING[group.id]
            return await app.sendGroupMessage(group, MessageChain.create([Plain("已取消")]))
    except asyncio.TimeoutError:
        del RUNNING[group.id]
        return await app.sendGroupMessage(group, MessageChain.create([Plain("等待超时")]))

    await app.sendGroupMessage(group, MessageChain.create([Plain("已开启本次答题，每一题有30秒答题时间，可随时发送取消终止进程")]))

    while True:
        word_data = await random_word(bookid)
        RUNNING[group.id] = word_data[0]
        pop = word_data[1].split("&")
        if pop == "":
            pop = ["/"]
        tran = word_data[2].split("&")
        word_len = len(word_data[0])
        wordinfo = []
        tran_num = 0
        for p in pop:
            wordinfo.append(f"[ {p} ] {tran[tran_num]}")
            tran_num += 1
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("本回合题目：\n"),
            Plain("\n".join(wordinfo))
        ]))
        for process in Process:
            try:
                if await asyncio.wait_for(inc.wait(waiter), timeout=30):
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"恭喜回答正确 {word_data[0]}")
                    ]))
                    await asyncio.sleep(1)
                    break
                else:
                    del RUNNING[group.id]
                    return await app.sendGroupMessage(group, MessageChain.create([Plain("已结束本次答题")]))

            except asyncio.TimeoutError:
                if process == 1:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"提示1\n这个单词由 {word_len} 个字母构成")
                    ]))
                elif process == 2:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"提示2\n这个单词的首字母是 {word_data[0][0]}")
                    ]))
                elif process == 3:
                    half = int(word_len / 2)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"提示3\n这个单词的前半部分为\n{word_data[0][:half]}")]))
                elif process == 4:
                    del RUNNING[group.id]
                    return await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"本次答案为：{word_data[0]}\n游戏已结束，请重新开启")
                    ]))