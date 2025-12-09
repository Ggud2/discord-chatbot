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

order_map = {}      # user_id -> index in order_list
order_list = []     # 순서대로 user_id 저장


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {synced}")
    except Exception as e:
        print(e)


@bot.tree.command(name="start", description="현재 채널 참여자에게 랜덤 번호를 부여하고 DM을 보냅니다.")
async def start(interaction: discord.Interaction):
    global order_map, order_list

    members = [m for m in interaction.channel.members if not m.bot]

    if len(members) < 2:
        await interaction.response.send_message("👀 최소 2명 이상이 있어야 게임을 시작할 수 있습니다.", ephemeral=True)
        return

    random.shuffle(members)
    order_list = [m.id for m in members]
    order_map = {m.id: i for i, m in enumerate(members)}

    await interaction.response.send_message(
        f"✨ 총 {len(members)}명이 참가했습니다! 순서가 무작위로 정해졌습니다. DM을 확인하세요!"
    )

    # 각 사용자에게 DM 보내기
    for i, member in enumerate(members):
        await member.send(f"당신은 **{i+1}번째** 입니다.")


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    # DM에서만 동작
    if message.guild is not None:
        return
    if message.author.bot:
        return
    if not order_map:
        return
    if message.author.id not in order_map:
        return

    idx = order_map[message.author.id]
    next_idx = (idx + 1) % len(order_list)   # 마지막 번호는 다시 첫 번째로 순환
    next_user_id = order_list[next_idx]

    next_user = await bot.fetch_user(next_user_id)
    await next_user.send(f"📩 전달된 메시지:\n\n{message.content}")

bot.run(TOKEN)