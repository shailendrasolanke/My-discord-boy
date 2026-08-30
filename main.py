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

# Flask Web Server
app = Flask('')

@app.route('/')
def home():
    return "Ultra Bot Active!"

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True)
    t.start()

# Database Setup
conn = sqlite3.connect('bot_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS economy (user_id INTEGER PRIMARY KEY, wallet INTEGER, bank INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS levels (user_id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS warns (user_id INTEGER, reason TEXT)''')
conn.commit()

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=".", intents=intents)

user_msg_count = {}

@bot.event
async def on_ready():
    print(f'🚀 Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name=".cmd | 50+ Features"))

# Auto-Mod / Anti-Spam / Anti-Link / XP System
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Anti-Link
    if not message.author.guild_permissions.administrator:
        if re.search(r"(https?://\S+|discord\.gg/\S+)", message.content):
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, Links allowed nahi hain!", delete_after=3)
            return

    # Anti-Spam
    uid = message.author.id
    now = datetime.datetime.now().timestamp()
    user_msg_count.setdefault(uid, []).append(now)
    user_msg_count[uid] = [t for t in user_msg_count[uid] if now - t < 4]
    if len(user_msg_count[uid]) > 5 and not message.author.guild_permissions.administrator:
        user_msg_count[uid] = []
        try:
            await message.author.timeout(datetime.timedelta(minutes=5), reason="Anti-Spam")
            await message.channel.send(f"🔇 {message.author.mention} auto-muted for spamming.", delete_after=4)
        except Exception:
            pass

    # Leveling XP System
    c.execute("INSERT OR IGNORE INTO levels VALUES (?, 0, 1)", (uid,))
    c.execute("UPDATE levels SET xp = xp + 5 WHERE user_id = ?", (uid,))
    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (uid,))
    xp, lvl = c.fetchone()
    if xp >= lvl * 100:
        c.execute("UPDATE levels SET level = level + 1, xp = 0 WHERE user_id = ?", (uid,))
        await message.channel.send(f"🎉 {message.author.mention} Leveled Up to **Level {lvl + 1}**!")
    conn.commit()

    await bot.process_commands(message)

# ----------------- COMMANDS LIST -----------------

# 📜 HELP & SYSTEM (1-5)
@bot.command()
async def cmd(ctx):
    embed = discord.Embed(title="📜 Mega Bot Commands (50+ Features)", color=0x00ff00)
    embed.add_field(name="🛡️ Security & Mod", value="`ban`, `unban`, `kick`, `mute`, `unmute`, `warn`, `warns`, `clearwarns`, `clear`, `slowmode`, `lockdown`, `unlock`, `nuke`, `roleadd`, `roleremove`", inline=False)
    embed.add_field(name="💰 Economy & Games", value="`balance`, `daily`, `work`, `beg`, `deposit`, `withdraw`, `pay`, `gamble`, `slots`, `coinflip`, `rob`", inline=False)
    embed.add_field(name="📈 Levels & Server Info", value="`rank`, `leaderboard`, `serverinfo`, `userinfo`, `avatar`, `botstats`, `ping`, `roleinfo`, `channelinfo`", inline=False)
    embed.add_field(name="🎉 Utility & Fun", value="`ticket`, `closeticket`, `poll`, `say`, `embed`, `meme`, `eightball`, `roll`, `choose`, `calculator`, `dm`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx): await ctx.send(f"🏓 Latency: {round(bot.latency * 1000)}ms")
@bot.command()
async def botstats(ctx): await ctx.send(f"📊 Servers: {len(bot.guilds)} | Users: {len(bot.users)}")

# 🛡️ SECURITY & MODERATION (6-20)
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="Violating rules"): await m.ban(reason=r); await ctx.send(f"⛔ Banned {m.name}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, uid: int):
    u = await bot.fetch_user(uid)
    await ctx.guild.unban(u)
    await ctx.send(f"🔓 Unbanned {u.name}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m: discord.Member, *, r="Violating rules"): await m.kick(reason=r); await ctx.send(f"🚨 Kicked {m.name}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, m: discord.Member, min: int = 10):
    await m.timeout(datetime.timedelta(minutes=min))
    await ctx.send(f"🔇 Muted {m.name} for {min}m")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, m: discord.Member): await m.timeout(None); await ctx.send(f"🔊 Unmuted {m.name}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, m: discord.Member, *, r="Warning"):
    c.execute("INSERT INTO warns VALUES (?, ?)", (m.id, r)); conn.commit()
    await ctx.send(f"⚠️ Warned {m.name} for `{r}`")

@bot.command()
async def warns(ctx, m: discord.Member):
    c.execute("SELECT reason FROM warns WHERE user_id = ?", (m.id,))
    res = c.fetchall()
    await ctx.send(f"📋 **{m.name}** has {len(res)} warnings.")

@bot.command()
@commands.has_permissions(administrator=True)
async def clearwarns(ctx, m: discord.Member):
    c.execute("DELETE FROM warns WHERE user_id = ?", (m.id,)); conn.commit()
    await ctx.send(f"🧹 Cleared warnings for {m.name}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amt: int = 5): await ctx.channel.purge(limit=amt + 1); await ctx.send(f"🧹 Cleared {amt} msgs", delete_after=2)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, sec: int): await ctx.channel.edit(slowmode_delay=sec); await ctx.send(f"⏱️ Slowmode: {sec}s")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lockdown(ctx): await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False); await ctx.send("🔒 Locked!")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx): await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True); await ctx.send("🔓 Unlocked!")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def nuke(ctx):
    pos = ctx.channel.position
    nc = await ctx.channel.clone()
    await ctx.channel.delete()
    await nc.edit(position=pos)
    await nc.send("💥 Channel Nuked!")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def roleadd(ctx, m: discord.Member, r: discord.Role): await m.add_roles(r); await ctx.send(f"✅ Added {r.name}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def roleremove(ctx, m: discord.Member, r: discord.Role): await m.remove_roles(r); await ctx.send(f"❌ Removed {r.name}")

# 💰 ECONOMY & GAMBLING (21-31)
@bot.command()
async def balance(ctx, m: discord.Member = None):
    m = m or ctx.author
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (m.id,))
    c.execute("SELECT wallet, bank FROM economy WHERE user_id = ?", (m.id,))
    w, b = c.fetchone()
    await ctx.send(f"💰 **{m.name}**: Wallet: `{w}` coins | Bank: `{b}` coins")

@bot.command()
async def daily(ctx):
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (ctx.author.id,))
    c.execute("UPDATE economy SET wallet = wallet + 500 WHERE user_id = ?", (ctx.author.id,))
    conn.commit()
    await ctx.send("🎁 Daily 500 coins claimed!")

@bot.command()
async def work(ctx):
    earn = random.randint(50, 200)
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (ctx.author.id,))
    c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earn, ctx.author.id))
    conn.commit()
    await ctx.send(f"💼 Worked and earned `{earn}` coins!")

@bot.command()
async def beg(ctx):
    earn = random.randint(10, 50)
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (ctx.author.id,))
    c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earn, ctx.author.id))
    conn.commit()
    await ctx.send(f"🥺 Someone gave you `{earn}` coins!")

@bot.command()
async def deposit(ctx, amt: int):
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amt:
        c.execute("UPDATE economy SET wallet = wallet - ?, bank = bank + ? WHERE user_id = ?", (amt, amt, ctx.author.id))
        conn.commit()
        await ctx.send(f"🏦 Deposited `{amt}` coins!")

@bot.command()
async def withdraw(ctx, amt: int):
    c.execute("SELECT bank FROM economy WHERE user_id = ?", (ctx.author.id,))
    b = c.fetchone()[0]
    if b >= amt:
        c.execute("UPDATE economy SET bank = bank - ?, wallet = wallet + ? WHERE user_id = ?", (amt, amt, ctx.author.id))
        conn.commit()
        await ctx.send(f"🏧 Withdrew `{amt}` coins!")

@bot.command()
async def pay(ctx, m: discord.Member, amt: int):
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amt:
        c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amt, ctx.author.id))
        c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (m.id,))
        c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amt, m.id))
        conn.commit()
        await ctx.send(f"💸 Paid `{amt}` coins to {m.name}!")

@bot.command()
async def gamble(ctx, amt: int):
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amt:
        win = random.choice([True, False])
        if win:
            c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amt, ctx.author.id))
            await ctx.send(f"🎉 You WON `{amt}` coins!")
        else:
            c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amt, ctx.author.id))
            await ctx.send(f"🔻 You LOST `{amt}` coins!")
        conn.commit()

@bot.command()
async def slots(ctx, amt: int):
    emojis = ["🎰", "🍎", "💎", "7️⃣"]
    r = [random.choice(emojis) for _ in range(3)]
    await ctx.send(f"[{' | '.join(r)}]")

@bot.command()
async def coinflip(ctx, choice: str):
    res = random.choice(["heads", "tails"])
    await ctx.send(f"🪙 Result: **{res}** - {'Won!' if choice.lower() == res else 'Lost!'}")

@bot.command()
async def rob(ctx, m: discord.Member):
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (m.id,))
    row = c.fetchone()
    if row and row[0] > 50:
        stolen = random.randint(10, row[0])
        c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (stolen, m.id))
        c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (stolen, ctx.author.id))
        conn.commit()
        await ctx.send(f"🥷 Stole `{stolen}` coins from {m.name}!")
    else: await ctx.send("❌ Target is too poor!")

# 📈 LEVELS & INFORMATION (32-40)
@bot.command()
async def rank(ctx, m: discord.Member = None):
    m = m or ctx.author
    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (m.id,))
    r = c.fetchone() or (0, 1)
    await ctx.send(f"📊 **{m.name}** | Level: `{r[1]}` | XP: `{r[0]}/{r[1]*100}`")

@bot.command()
async def leaderboard(ctx):
    c.execute("SELECT user_id, level FROM levels ORDER BY level DESC LIMIT 5")
    top = c.fetchall()
    msg = "\n".join([f"{i+1}. <@{u[0]}> - Level {u[1]}" for i, u in enumerate(top)])
    await ctx.send(f"🏆 **Top 5 Leaderboard**\n{msg}")

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    await ctx.send(f"🏰 **{g.name}** | Members: `{g.member_count}` | Created: `{g.created_at.strftime('%Y-%m-%d')}`")

@bot.command()
async def userinfo(ctx, m: discord.Member = None):
    m = m or ctx.author
    await ctx.send(f"👤 **{m.name}** | ID: `{m.id}` | Joined: `{m.joined_at.strftime('%Y-%m-%d')}`")

@bot.command()
async def avatar(ctx, m: discord.Member = None):
    m = m or ctx.author
    await ctx.send(m.display_avatar.url)

@bot.command()
async def roleinfo(ctx, r: discord.Role): await ctx.send(f"🎭 **{r.name}** | ID: `{r.id}` | Color: `{r.color}`")
@bot.command()
async def channelinfo(ctx): await ctx.send(f"📺 **{ctx.channel.name}** | ID: `{ctx.channel.id}`")

# 🎫 UTILITY & TICKETS (41-45)
@bot.command()
async def ticket(ctx):
    ch = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}")
    await ch.set_permissions(ctx.guild.default_role, read_messages=False)
    await ch.set_permissions(ctx.author, read_messages=True)
    await ch.send(f"🎫 Ticket opened for {ctx.author.mention}. Use `.closeticket` to finish.")

@bot.command()
async def closeticket(ctx):
    if "ticket-" in ctx.channel.name: await ctx.channel.delete()

@bot.command()
async def poll(ctx, *, q: str):
    msg = await ctx.send(f"📊 **POLL:** {q}")
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, *, txt: str): await ctx.message.delete(); await ctx.send(txt)

@bot.command()
@commands.has_permissions(administrator=True)
async def embed(ctx, *, txt: str):
    await ctx.send(embed=discord.Embed(description=txt, color=0x00ffff))

# 🎉 FUN & GAMES (46-50)
@bot.command()
async def eightball(ctx, *, q: str):
    ans = ["Yes", "No", "Definitely", "Ask again later", "Never"]
    await ctx.send(f"🎱 **Q:** {q}\n**A:** {random.choice(ans)}")

@bot.command()
async def roll(ctx, dice: str = "1d6"):
    await ctx.send(f"🎲 Rolled: `{random.randint(1, 6)}`")

@bot.command()
async def choose(ctx, *opts):
    await ctx.send(f"🤔 Choice: `{random.choice(opts)}`")

@bot.command()
async def calculator(ctx, exp: str):
    try: await ctx.send(f"🧮 Result: `{eval(exp)}`")
    except Exception: await ctx.send("❌ Invalid expression")

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, m: discord.Member, *, txt: str):
    await m.send(f"📩 Message from **{ctx.guild.name}**: {txt}")
    await ctx.send("✅ Sent!")

async def main():
    keep_alive()
    async with bot:
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
