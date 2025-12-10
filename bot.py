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
active = False      # 현재 진행중 여부
game_channel = None # 게임이 실행된 채널 객체 저장


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {synced}")
    except Exception as e:
        print(e)


def shuffle_order():
    """order_list를 재랜덤 → order_map 업데이트"""
    global order_list, order_map
    random.shuffle(order_list)
    order_map = {uid: idx for idx, uid in enumerate(order_list)}

@bot.tree.command(name="시작", description="현재 채널 참여자에게 랜덤 번호를 부여하고 DM을 보냅니다.")
async def start(interaction: discord.Interaction):
    global order_map, order_list, active, game_channel

    game_channel = interaction.channel
    
    members = [m for m in interaction.channel.members if not m.bot]

    if len(members) < 2:
        await interaction.response.send_message("👀 최소 2명 이상이 있어야 게임을 시작할 수 있습니다.", ephemeral=True)
        return

    order_list = [m.id for m in members]
    shuffle_order()
    active = True

    await interaction.response.send_message(
        f"✨ 총 {len(members)}명이 참가했습니다! 순서가 무작위로 정해졌습니다. DM을 확인하세요!"
    )

    # 각 사용자에게 DM 보내기
    for i, uid in enumerate(order_list):
        user = await bot.fetch_user(uid)
        await user.send(f"당신은 **{i+1}번째** 입니다.")
        await user.send(f"여기에 입력하는 채팅은 **{(i+1) % len(members)+1}번**에게 전달됩니다.")


@bot.tree.command(name="랜덤", description="현재 참가자 그대로 순서를 재랜덤합니다.")
async def shuffle(interaction: discord.Interaction):
    global active

    if not active:
        await interaction.response.send_message("⚠ 게임이 진행 중이 아닙니다. 먼저 /시작 을 사용하세요.", ephemeral=True)
        return

    shuffle_order()

    await interaction.response.send_message("🔀 순서를 다시 랜덤으로 정했습니다! DM을 확인하세요!")

    for i, uid in enumerate(order_list):
        user = await bot.fetch_user(uid)
        await user.send(f"🔀 순서가 다시 정해졌습니다.\n당신은 **{i + 1}번째** 입니다.")
        await user.send(f"여기에 입력하는 채팅은 **{(i+1) % len(order_list) + 1}번**에게 전달됩니다.")


@bot.tree.command(name="종료", description="게임을 종료하고 메시지 전달 기능을 비활성화합니다.")
async def stop(interaction: discord.Interaction):
    global order_map, order_list, active

    if not active:
        await interaction.response.send_message("⚠ 종료할 게임이 없습니다.", ephemeral=True)
        return

    order_map = {}
    order_list = []
    active = False

    await interaction.response.send_message("🛑 게임이 종료되었습니다. 메시지 전달 기능이 비활성화됩니다.")


@bot.tree.command(name="모두", description="모든 참가자에게 메시지를 전송합니다.(단체방에 전송)")
@app_commands.describe(
    message="보낼 메시지(선택)",
    attachment="이미지 또는 파일(선택)"
)
async def everyone(interaction: discord.Interaction, message: str = "", attachment: discord.Attachment = None):
    global active, order_map, order_list, game_channel

    if not active:
        await interaction.response.send_message("⚠ 게임이 진행 중이 아닙니다. 먼저 /시작 을 사용하세요.", ephemeral=True)
        return

    if interaction.user.id not in order_map:
        await interaction.response.send_message("⚠ 당신은 게임 참가자가 아닙니다.", ephemeral=True)
        return

    if not game_channel:
        await interaction.response.send_message("⚠ 단체 채널 정보를 찾지 못했습니다.", ephemeral=True)
        return

    idx = order_map[interaction.user.id]

    if message.strip():
        broadcast_msg = f"📢 **{idx+1}번의 메시지:** {message}"
    else:
        broadcast_msg = f"📢 **{idx+1}번의 메시지:**"

    # 이미지/파일 있는 경우
    if attachment:
        file = await attachment.to_file()
        await game_channel.send(broadcast_msg, file=file)
    else:
        # 텍스트만 있는 경우
        if message.strip():
            await game_channel.send(broadcast_msg)
        # 둘 다 없는 경우
        else:
            await interaction.response.send_message("⚠ 메시지 또는 첨부파일 하나는 있어야 합니다.", ephemeral=True)

    await interaction.response.send_message("📨 메시지가 전송되었습니다.", ephemeral=True)


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if not active:
        return

    # DM에서만 전달
    if message.guild is not None:
        return
    if message.author.bot:
        return
    if message.author.id not in order_map:
        return

    idx = order_map[message.author.id]
    
    next_idx = (idx + 1) % len(order_list)
    next_id = order_list[next_idx]

    next_user = await bot.fetch_user(next_id)
    
    content = f"📩 {message.content}" if message.content.strip() else "📩"

    if message.attachments:
        files = []
        for att in message.attachments:
            fp = await att.to_file()
            files.append(fp)
        await next_user.send(content, files = files)
    else:
        await next_user.send(content)

bot.run(TOKEN)