import os
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import app_commands
import random

load_dotenv() # .env 파일 읽기
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.guilds = True
intents.dm_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

order_map = {}  # user_id -> order number
order_list = [] # [user_id1, user_id2, user_id3]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command(name="시작!")
async def start(ctx):
    global order_map, order_list

    members = [member for member in ctx.channel.members if not member.bot]

    if len(members) != 3:
        await ctx.send("👀 참가 인원은 정확히 3명이어야 합니다.")
        return

    random.shuffle(members)
    order_list = [m.id for m in members]

    order_map = {member.id: i for i, member in enumerate(members)}

    await ctx.send("✨ 순서가 무작위로 정해졌습니다. 각자에게 DM을 확인하세요!")

    for i, member in enumerate(members):
        await member.send(f"당신은 **{i+1}번째** 입니다.")


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    # DM 에서만 메시지 전달
    if message.guild is not None:
        return
    if message.author.bot:
        return
    if not order_map:
        return

    player_id = message.author.id

    if player_id not in order_map:
        return

    current_order = order_map[player_id]
    next_order = (current_order + 1) % 3
    next_id = order_list[next_order]

    next_user = await bot.fetch_user(next_id)
    await next_user.send(f"📩 전달된 메시지:\n\n{message.content}")

bot.run(TOKEN)