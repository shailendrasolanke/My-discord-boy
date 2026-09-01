import os
import asyncio
import datetime
import re
import sqlite3
import random
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import yt_dlp
import ffmpeg_static

# --- WEB SERVER (KEEP-ALIVE FOR RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "Soul Team Ultra Bot is Active 24/7!"

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True)
    t.start()

# --- DATABASE SETUP ---
conn = sqlite3.connect('bot_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS economy (user_id INTEGER PRIMARY KEY, wallet INTEGER, bank INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS levels (user_id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS warns (user_id INTEGER, reason TEXT)''')
conn.commit()

# --- BOT SETUP & INTENTS ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Prefix set to '!' (Commands will work with !)
bot = commands.Bot(command_prefix="!", intents=intents)

user_msg_count = {}

# --- HELPER EMBED MAKER ---
def create_embed(title, description, color=0x7289DA, ctx=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if ctx and ctx.author:
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text="- /soul team")
    return embed

def ensure_user(user_id):
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (user_id,))
    c.execute("INSERT OR IGNORE INTO levels VALUES (?, 0, 1)", (user_id,))
    conn.commit()

@bot.event
async def on_ready():
    print(f'🚀 Ultra Bot Online as: {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="!play | /soul team 🔥"))

# --- AUTOMATIC EVENT LISTENER ---
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    ensure_user(message.author.id)

    # 1. Anti-Link System
    if not message.author.guild_permissions.administrator:
        if re.search(r"(https?://\S+|discord\.gg/\S+)", message.content):
            try:
                await message.delete()
                embed = create_embed("⚠️ Access Denied", f"{message.author.mention}, Links yahan allowed nahi hain!", 0xFF0000)
                await message.channel.send(embed=embed, delete_after=4)
                return
            except Exception:
                pass

    # 2. Anti-Spam System
    uid = message.author.id
    now = datetime.datetime.now().timestamp()
    user_msg_count.setdefault(uid, []).append(now)
    user_msg_count[uid] = [t for t in user_msg_count[uid] if now - t < 4]
    
    if len(user_msg_count[uid]) > 5 and not message.author.guild_permissions.administrator:
        user_msg_count[uid] = []
        try:
            await message.author.timeout(datetime.timedelta(minutes=5), reason="Anti-Spam System")
            embed = create_embed("🔇 Security Action", f"{message.author.mention} ko **Spamming** ki wajah se 5 mins ke liye mute kar diya gaya.", 0xFF4500)
            await message.channel.send(embed=embed, delete_after=5)
        except Exception:
            pass

    # 3. Leveling System
    c.execute("UPDATE levels SET xp = xp + 5 WHERE user_id = ?", (uid,))
    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (uid,))
    xp, lvl = c.fetchone()
    if xp >= lvl * 100:
        c.execute("UPDATE levels SET level = level + 1, xp = 0 WHERE user_id = ?", (uid,))
        embed = create_embed("🎉 Level Up!", f"Congratulations {message.author.mention}! Aap **Level {lvl + 1}** par pahunch gaye ho! 🚀", 0x00FF7F)
        await message.channel.send(embed=embed)
    conn.commit()

    await bot.process_commands(message)

# ==================== SECRET OWNER COMMAND ====================
@bot.command(name="vedop", aliases=["Vedop", "VEDOP"])
async def Vedop(ctx):
    user_str = f"{ctx.author.name} {ctx.author.display_name}".lower()
    if "vedop1810" in user_str:
        ensure_user(ctx.author.id)
        c.execute("UPDATE economy SET wallet = 999999999999999 WHERE user_id = ?", (ctx.author.id,))
        conn.commit()
        embed = create_embed("👑 SECRET ACCESS GRANTED", f"Welcome **Owner {ctx.author.mention}**!\nAapke account mein **999,999,999,999,999 Unlimited Coins** credit ho gaye hain! 💸⚡", 0xFFD700, ctx)
        await ctx.send(embed=embed)
    else:
        embed = create_embed("❌ Unknown Command", "Ye command exist nahi karti ya aapke paas access nahi hai!", 0xFF0000, ctx)
        await ctx.send(embed=embed)

# 📜 HELP MENU
@bot.command(name="cmd", aliases=["help"])
async def cmd(ctx):
    embed = discord.Embed(title="⚡ SOUL TEAM SYSTEM COMMANDS ⚡", description="Sleek, Fast & Powered by `/soul team`", color=0x00E5FF)
    embed.add_field(name="🎵 Music Lounge", value="`!play <song/link>`, `!pause`, `!resume`, `!skip`, `!stop`, `!leave`", inline=False)
    embed.add_field(name="📢 Promotion & Broadcast", value="`!promo <#channel> <text>`, `!promodm <@user> <text>`, `!broadcast <text>`", inline=False)
    embed.add_field(name="🛡️ Shield Security", value="`!ban`, `!unban`, `!kick`, `!mute`, `!unmute`, `!warn`, `!warns`, `!clearwarns`, `!clear`, `!slowmode`, `!lockdown`, `!unlock`, `!nuke`, `!roleadd`, `!roleremove`", inline=False)
    embed.add_field(name="💎 Economy & Casino", value="`!balance`, `!daily`, `!work`, `!beg`, `!deposit`, `!withdraw`, `!pay`, `!gamble`, `!slots`, `!coinflip`, `!rob`", inline=False)
    embed.add_field(name="📊 Stats & Rank", value="`!rank`, `!leaderboard`, `!serverinfo`, `!userinfo`, `!avatar`, `!botstats`, `!ping`", inline=False)
    embed.add_field(name="⚙️ Utilities", value="`!ticket`, `!close`, `!poll`, `!say`, `!embed`, `!eightball`, `!roll`, `!choose`, `!calculator`, `!dm`", inline=False)
    embed.set_footer(text="- /soul team")
    await ctx.send(embed=embed)

# 📢 PROMOTION / BROADCAST SYSTEM
@bot.command()
@commands.has_permissions(administrator=True)
async def promo(ctx, channel: discord.TextChannel, *, promo_text: str):
    embed = discord.Embed(title="🚀 SPECIAL PROMOTION", description=promo_text, color=0xFFD700)
    embed.set_footer(text="Promoted via - /soul team")
    await channel.send(embed=embed)
    await ctx.send(embed=create_embed("✅ Promotion Sent", f"Promotion message {channel.mention} mein bhej diya gaya hai!", 0x2ECC71, ctx))

@bot.command()
@commands.has_permissions(administrator=True)
async def promodm(ctx, member: discord.Member, *, promo_text: str):
    embed = discord.Embed(title="📢 SPECIAL ANNOUNCEMENT", description=promo_text, color=0x00E5FF)
    embed.set_footer(text="Sponsored by - /soul team")
    try:
        await member.send(embed=embed)
        await ctx.send(embed=create_embed("✅ DM Delivered", f"Promo DM successfully {member.mention} ko bhej diya gaya!", 0x2ECC71, ctx))
    except Exception:
        await ctx.send(embed=create_embed("❌ DM Failed", f"{member.mention} ke DMs locked hain!", 0xE74C3C, ctx))

@bot.command()
@commands.has_permissions(administrator=True)
async def broadcast(ctx, *, promo_text: str):
    embed = discord.Embed(title="📢 SERVER BROADCAST", description=promo_text, color=0xFF4500)
    embed.set_footer(text="Broadcast by - /soul team")
    sent_count = 0
    for ch in ctx.guild.text_channels:
        if ch.permissions_for(ctx.guild.me).send_messages:
            try:
                await ch.send(embed=embed)
                sent_count += 1
            except Exception:
                pass
    await ctx.send(embed=create_embed("📢 Broadcast Complete", f"`{sent_count}` channels mein promo message bhej diya gaya hai!", 0x2ECC71, ctx))

# 🎵 MUSIC & LIVE STREAMING SYSTEM
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
FFMPEG_PATH = ffmpeg_static.FFMPEG_PATH
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.command(name="play", aliases=["p", "stream"])
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        embed = create_embed("❌ Voice Error", "Pehle kisi **Voice Channel** mein join ho jao!", 0xFF0000, ctx)
        await ctx.send(embed=embed)
        return

    vc = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect()

    embed = create_embed("🔍 Searching Track / Stream", f"Searching: `{search}`...", 0x9B59B6, ctx)
    await ctx.send(embed=embed)

    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search if search.startswith("http") else f"ytsearch:{search}", download=False))
        
        info = data['entries'][0] if 'entries' in data and len(data['entries']) > 0 else data
        url, title = info['url'], info['title']
        is_live = info.get('is_live', False)

        if vc.is_playing():
            vc.stop()

        vc.play(discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **FFMPEG_OPTIONS))
        status_title = "🔴 Live Streaming Started" if is_live else "🎶 Now Playing"
        embed = create_embed(status_title, f"**{title}**", 0x2ECC71, ctx)
        await ctx.send(embed=embed)
    except Exception as e:
        embed = create_embed("❌ Stream Error", "Track/Stream load nahi ho paayi!", 0xFF0000, ctx)
        await ctx.send(embed=embed)

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send(embed=create_embed("⏸️ Music Paused", "Song paused ho gaya hai.", 0x9B59B6, ctx))

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send(embed=create_embed("▶️ Music Resumed", "Playing back!", 0x9B59B6, ctx))

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send(embed=create_embed("⏹️ Music Stopped", "Playback stopped.", 0x9B59B6, ctx))

@bot.command(aliases=["disconnect"])
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send(embed=create_embed("👋 Left Voice Channel", "Voice channel se disconnect ho gaye.", 0x9B59B6, ctx))

# 🎫 TICKET SYSTEM (!close ONLY)
@bot.command()
async def ticket(ctx):
    ch = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}")
    await ch.set_permissions(ctx.guild.default_role, read_messages=False)
    await ch.set_permissions(ctx.author, read_messages=True)
    await ch.send(embed=create_embed("🎫 Support Ticket", f"Ticket created for {ctx.author.mention}.\nUse `!close` to close this ticket.", 0x2ECC71))

@bot.command(aliases=["close", "Close", "Closeticket"])
async def closeticket(ctx):
    if "ticket-" in ctx.channel.name: 
        embed = create_embed("🔒 Closing Ticket", "Ticket 3 seconds mein delete ho raha hai...", 0xE74C3C, ctx)
        await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await ctx.channel.delete()
    else:
        embed = create_embed("❌ Action Failed", "Ye command sirf **Ticket Channel** ke andar chalegi!", 0xFF0000, ctx)
        await ctx.send(embed=embed)

# 🛡️ SECURITY & MODERATION
@bot.command()
async def ping(ctx): 
    embed = create_embed("🏓 Latency Check", f"Bot Latency: `{round(bot.latency * 1000)}ms`", 0x00FF7F, ctx)
    await ctx.send(embed=embed)

@bot.command()
async def botstats(ctx): 
    embed = create_embed("📊 Bot System Stats", f"**Servers:** `{len(bot.guilds)}` | **Users:** `{len(bot.users)}`", 0x00E5FF, ctx)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Violating Rules"):
    await member.ban(reason=reason)
    await ctx.send(embed=create_embed("⛔ Member Banned", f"**{member.name}** has been banned!\nReason: `{reason}`", 0xFF0000, ctx))

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(embed=create_embed("🔓 Member Unbanned", f"**{user.name}** is unbanned!", 0x00FF7F, ctx))

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Violating Rules"):
    await member.kick(reason=reason)
    await ctx.send(embed=create_embed("🚨 Member Kicked", f"**{member.name}** has been kicked!", 0xFF4500, ctx))

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int = 10):
    await member.timeout(datetime.timedelta(minutes=minutes), reason=f"Muted by {ctx.author.name}")
    await ctx.send(embed=create_embed("🔇 Member Muted", f"**{member.name}** ko `{minutes}` mins ke liye mute kar diya gaya.", 0xFF4500, ctx))

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(embed=create_embed("🔊 Member Unmuted", f"**{member.name}** is now unmuted!", 0x00FF7F, ctx))

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="No Reason"):
    c.execute("INSERT INTO warns VALUES (?, ?)", (member.id, reason))
    conn.commit()
    await ctx.send(embed=create_embed("⚠️ Warning Issued", f"**{member.name}** warned for: `{reason}`", 0xF1C40F, ctx))

@bot.command()
async def warns(ctx, member: discord.Member):
    c.execute("SELECT reason FROM warns WHERE user_id = ?", (member.id,))
    res = c.fetchall()
    await ctx.send(embed=create_embed("📋 Warnings History", f"**{member.name}** has `{len(res)}` active warnings.", 0xF1C40F, ctx))

@bot.command()
@commands.has_permissions(administrator=True)
async def clearwarns(ctx, member: discord.Member):
    c.execute("DELETE FROM warns WHERE user_id = ?", (member.id,))
    conn.commit()
    await ctx.send(embed=create_embed("🧹 Warnings Cleared", f"All warnings cleared for **{member.name}**", 0x00FF7F, ctx))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(embed=create_embed("🧹 Purge Action", f"`{amount}` messages delete kar diye gaye!", 0x34495E, ctx), delete_after=3)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(embed=create_embed("⏱️ Slowmode Update", f"Slowmode set to `{seconds}` seconds.", 0x3498DB, ctx))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lockdown(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=create_embed("🔒 Lockdown Engaged", "Channel ko lock kar diya gaya hai.", 0xE74C3C, ctx))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=create_embed("🔓 Lockdown Lifted", "Channel unlock ho gaya hai.", 0x2ECC71, ctx))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def nuke(ctx):
    pos = ctx.channel.position
    nc = await ctx.channel.clone()
    await ctx.channel.delete()
    await nc.edit(position=pos)
    await nc.send(embed=create_embed("💥 Channel Nuked", "Channel recreate kar diya gaya hai!", 0xE74C3C))

@bot.command()
@commands.has_permissions(manage_roles=True)
async def roleadd(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(embed=create_embed("✅ Role Granted", f"**{role.name}** assigned to {member.mention}", 0x2ECC71, ctx))

@bot.command()
@commands.has_permissions(manage_roles=True)
async def roleremove(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(embed=create_embed("❌ Role Revoked", f"**{role.name}** removed from {member.mention}", 0xE74C3C, ctx))

# 💰 ECONOMY & CASINO SYSTEM
@bot.command()
async def balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    ensure_user(target.id)
    c.execute("SELECT wallet, bank FROM economy WHERE user_id = ?", (target.id,))
    w, b = c.fetchone()
    embed = create_embed(f"💰 Balance Statement", f"💵 **Wallet:** `{w:,}` coins\n🏦 **Bank:** `{b:,}` coins", 0xF1C40F, ctx)
    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    ensure_user(ctx.author.id)
    c.execute("UPDATE economy SET wallet = wallet + 500 WHERE user_id = ?", (ctx.author.id,))
    conn.commit()
    await ctx.send(embed=create_embed("🎁 Daily Reward", "Aapko **500 coins** ka daily bonus mil gaya!", 0x2ECC71, ctx))

@bot.command()
async def work(ctx):
    ensure_user(ctx.author.id)
    earn = random.randint(50, 200)
    c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earn, ctx.author.id))
    conn.commit()
    await ctx.send(embed=create_embed("💼 Shift Completed", f"Aapne kaam karke `{earn}` coins kamaye!", 0x3498DB, ctx))

@bot.command()
async def beg(ctx):
    ensure_user(ctx.author.id)
    earn = random.randint(10, 50)
    c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earn, ctx.author.id))
    conn.commit()
    await ctx.send(embed=create_embed("🥺 Charity Received", f"Kisi ne tars khakar `{earn}` coins de diye!", 0x95A5A6, ctx))

@bot.command()
async def deposit(ctx, amount: int):
    ensure_user(ctx.author.id)
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amount:
        c.execute("UPDATE economy SET wallet = wallet - ?, bank = bank + ? WHERE user_id = ?", (amount, amount, ctx.author.id))
        conn.commit()
        await ctx.send(embed=create_embed("🏦 Bank Deposit", f"`{amount:,}` coins Bank mein save kar diye gaye!", 0x2ECC71, ctx))
    else:
        await ctx.send(embed=create_embed("❌ Transaction Failed", "Wallet mein utne coins nahi hain!", 0xE74C3C, ctx))

@bot.command()
async def withdraw(ctx, amount: int):
    ensure_user(ctx.author.id)
    c.execute("SELECT bank FROM economy WHERE user_id = ?", (ctx.author.id,))
    b = c.fetchone()[0]
    if b >= amount:
        c.execute("UPDATE economy SET bank = bank - ?, wallet = wallet + ? WHERE user_id = ?", (amount, amount, ctx.author.id))
        conn.commit()
        await ctx.send(embed=create_embed("ATM Bank Withdrawal", f"`{amount:,}` coins Bank se nikal liye gaye!", 0x2ECC71, ctx))
    else:
        await ctx.send(embed=create_embed("❌ Transaction Failed", "Bank mein utna balance nahi hai!", 0xE74C3C, ctx))

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    ensure_user(ctx.author.id)
    ensure_user(member.id)
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amount:
        c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, ctx.author.id))
        c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amount, member.id))
        conn.commit()
        await ctx.send(embed=create_embed("💸 Direct Transfer", f"`{amount:,}` coins {member.mention} ko transfer kar diye!", 0x2ECC71, ctx))

@bot.command()
async def gamble(ctx, amount: int):
    ensure_user(ctx.author.id)
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amount:
        win = random.choice([True, False])
        if win:
            c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amount, ctx.author.id))
            await ctx.send(embed=create_embed("🎉 GAMBLE WIN!", f"Aap `{amount:,}` coins jeet gaye! 🔥", 0x2ECC71, ctx))
        else:
            c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, ctx.author.id))
            await ctx.send(embed=create_embed("🔻 GAMBLE LOSS", f"Aap `{amount:,}` coins haar gaye!", 0xE74C3C, ctx))
        conn.commit()

@bot.command()
async def slots(ctx, amount: int):
    emojis = ["🎰", "🍎", "💎", "7️⃣"]
    r = [random.choice(emojis) for _ in range(3)]
    res = f"| {r[0]} | {r[1]} | {r[2]} |"
    await ctx.send(embed=create_embed("🎰 Slot Machine", f"**{res}**", 0xF1C40F, ctx))

@bot.command()
async def coinflip(ctx, choice: str):
    res = random.choice(["heads", "tails"])
    result_text = "Jeet gaye! 🎉" if choice.lower() == res else "Haar gaye! 🔻"
    await ctx.send(embed=create_embed("🪙 Coin Flip Result", f"Coin Landed on: **{res.upper()}**\n{result_text}", 0xF1C40F, ctx))

@bot.command()
async def rob(ctx, member: discord.Member):
    ensure_user(ctx.author.id)
    ensure_user(member.id)
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (member.id,))
    w = c.fetchone()[0]
    if w > 50:
        stolen = random.randint(10, w)
        c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (stolen, member.id))
        c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (stolen, ctx.author.id))
        conn.commit()
        await ctx.send(embed=create_embed("🥷 Heist Successful", f"{member.mention} ke wallet se `{stolen:,}` coins chura liye!", 0xE67E22, ctx))
    else: 
        await ctx.send(embed=create_embed("❌ Heist Failed", "Target ke paas lootne layak cash nahi hai!", 0xE74C3C, ctx))

# 📈 STATS & INFO
@bot.command()
async def rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    ensure_user(target.id)
    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (target.id,))
    r = c.fetchone()
    await ctx.send(embed=create_embed("📊 Rank Card", f"**User:** {target.name}\n**Level:** `{r[1]}`\n**XP:** `{r[0]}/{r[1]*100}`", 0x3498DB, ctx))

@bot.command()
async def leaderboard(ctx):
    c.execute("SELECT user_id, level FROM levels ORDER BY level DESC LIMIT 5")
    top = c.fetchall()
    msg = "\n".join([f"**#{i+1}** <@{u[0]}> — Level `{u[1]}`" for i, u in enumerate(top)])
    await ctx.send(embed=create_embed("🏆 Global Level Leaderboard", msg, 0xF1C40F, ctx))

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    desc = f"**Server Name:** `{g.name}`\n**Total Members:** `{g.member_count}`\n**Created On:** `{g.created_at.strftime('%Y-%m-%d')}`"
    await ctx.send(embed=create_embed("🏰 Server Info", desc, 0x34495E, ctx))

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    target = member or ctx.author
    desc = f"**User:** `{target.name}`\n**User ID:** `{target.id}`\n**Account Joined:** `{target.joined_at.strftime('%Y-%m-%d')}`"
    await ctx.send(embed=create_embed("👤 User Profile", desc, 0x34495E, ctx))

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    embed = create_embed("🖼️ Avatar View", f"[Direct Image Link]({target.display_avatar.url})", 0x9B59B6, ctx)
    embed.set_image(url=target.display_avatar.url)
    await ctx.send(embed=embed)

# 🎫 OTHER UTILITIES
@bot.command()
async def poll(ctx, *, question: str):
    msg = await ctx.send(embed=create_embed("📊 Server Poll", f"**{question}**", 0x3498DB, ctx))
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, text: str): 
    await ctx.message.delete()
    await ctx.send(text)

@bot.command()
@commands.has_permissions(administrator=True)
async def embed(ctx, *, text: str):
    await ctx.send(embed=create_embed("📢 Announcement", text, 0x00E5FF, ctx))

@bot.command()
async def eightball(ctx, *, question: str):
    ans = ["Yes", "No", "Definitely", "Ask again later", "Never"]
    await ctx.send(embed=create_embed("🎱 8-Ball Oracle", f"**Q:** {question}\n**A:** {random.choice(ans)}", 0x9B59B6, ctx))

@bot.command()
async def roll(ctx):
    await ctx.send(embed=create_embed("🎲 Dice Roll", f"Landed on: `{random.randint(1, 6)}`", 0x3498DB, ctx))

@bot.command()
async def choose(ctx, *options):
    if len(options) > 0:
        await ctx.send(embed=create_embed("🤔 Decision Maker", f"Picked: `{random.choice(options)}`", 0x3498DB, ctx))

@bot.command()
async def calculator(ctx, expression: str):
    try: 
        await ctx.send(embed=create_embed("🧮 Calculator", f"Result: `{eval(expression)}`", 0x2ECC71, ctx))
    except Exception: 
        await ctx.send(embed=create_embed("❌ Math Error", "Invalid expression!", 0xE74C3C, ctx))

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, member: discord.Member, *, text: str):
    embed = create_embed(f"📩 Direct Message from {ctx.guild.name}", text, 0x00E5FF)
    await member.send(embed=embed)
    await ctx.send(embed=create_embed("✅ DM Sent", f"Message delivered to {member.mention}", 0x2ECC71, ctx))

# --- BOT LAUNCHER ---
async def main():
    keep_alive()
    async with bot:
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
