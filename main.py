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

# --- WEB SERVER (KEEP-ALIVE FOR RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "Ultra Bot is Active 24/7!"

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True)
    t.start()

# --- DATABASE SETUP (SQLITE) ---
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

bot = commands.Bot(command_prefix=".", intents=intents)

user_msg_count = {}

@bot.event
async def on_ready():
    print(f'🚀 Ultra Security & Economy Bot Online as: {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name=".cmd | Multi-Feature Guard 🛡️"))

# --- AUTOMATIC EVENT LISTENER (ANTI-LINK, ANTI-SPAM & XP SYSTEM) ---
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # 1. Anti-Link System
    if not message.author.guild_permissions.administrator:
        if re.search(r"(https?://\S+|discord\.gg/\S+)", message.content):
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, Links here are not allowed!", delete_after=3)
            return

    # 2. Anti-Spam System
    uid = message.author.id
    now = datetime.datetime.now().timestamp()
    user_msg_count.setdefault(uid, []).append(now)
    user_msg_count[uid] = [t for t in user_msg_count[uid] if now - t < 4]
    
    if len(user_msg_count[uid]) > 5 and not message.author.guild_permissions.administrator:
        user_msg_count[uid] = []
        try:
            await message.author.timeout(datetime.timedelta(minutes=5), reason="Anti-Spam System")
            await message.channel.send(f"🔇 {message.author.mention} was auto-muted for 5 minutes (Spamming).", delete_after=4)
        except Exception:
            pass

    # 3. Leveling System (XP Generation)
    c.execute("INSERT OR IGNORE INTO levels VALUES (?, 0, 1)", (uid,))
    c.execute("UPDATE levels SET xp = xp + 5 WHERE user_id = ?", (uid,))
    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (uid,))
    xp, lvl = c.fetchone()
    if xp >= lvl * 100:
        c.execute("UPDATE levels SET level = level + 1, xp = 0 WHERE user_id = ?", (uid,))
        await message.channel.send(f"🎉 {message.author.mention} Leveled Up to **Level {lvl + 1}**!")
    conn.commit()

    await bot.process_commands(message)

# ==================== COMMANDS LIST ====================

# 👑 SPECIAL OWNER COMMAND (UNLIMITED COINS FOR VEDOP1810.)
@bot.command()
async def Vedop(ctx):
    # 'vedop1810.' aur 'vedop1810' dono check karega
    if ctx.author.name.lower() in ["vedop1810.", "vedop1810"]:
        c.execute("INSERT OR IGNORE INTO economy VALUES (?, 0, 0)", (ctx.author.id,))
        c.execute("UPDATE economy SET wallet = 999999999999999 WHERE user_id = ?", (ctx.author.id,))
        conn.commit()
        await ctx.send(f"👑 **Welcome Owner {ctx.author.mention}!**\nApke account (`{ctx.author.name}`) me **999,999,999,999,999 Unlimited Coins** add ho gaye hain! 💸⚡")
    else:
        await ctx.send(f"❌ Ye command sirf **vedop1810.** ke liye reserved hai! (Aapka ID: `{ctx.author.name}`)")

# 📜 HELP & SYSTEM MENU
@bot.command()
async def cmd(ctx):
    embed = discord.Embed(title="📜 Mega Bot Commands Suite", color=0x00ff00)
    embed.add_field(name="👑 Owner Special", value="`.Vedop` - Grant Unlimited Coins (vedop1810. only)", inline=False)
    embed.add_field(name="🛡️ Security & Mod", value="`.ban`, `.unban`, `.kick`, `.mute`, `.unmute`, `.warn`, `.warns`, `.clearwarns`, `.clear`, `.slowmode`, `.lockdown`, `.unlock`, `.nuke`, `.roleadd`, `.roleremove`", inline=False)
    embed.add_field(name="💰 Economy & Games", value="`.balance`, `.daily`, `.work`, `.beg`, `.deposit`, `.withdraw`, `.pay`, `.gamble`, `.slots`, `.coinflip`, `.rob`", inline=False)
    embed.add_field(name="📈 Levels & Info", value="`.rank`, `.leaderboard`, `.serverinfo`, `.userinfo`, `.avatar`, `.botstats`, `.ping`, `.roleinfo`, `.channelinfo`", inline=False)
    embed.add_field(name="🎉 Utility & Fun", value="`.ticket`, `.closeticket`, `.poll`, `.say`, `.embed`, `.eightball`, `.roll`, `.choose`, `.calculator`, `.dm`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx): 
    await ctx.send(f"🏓 Latency: `{round(bot.latency * 1000)}ms`")

@bot.command()
async def botstats(ctx): 
    await ctx.send(f"📊 Servers: `{len(bot.guilds)}` | Users: `{len(bot.users)}`")

# 🛡️ SECURITY & MODERATION COMMANDS
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Violating rules"):
    await member.ban(reason=reason)
    await ctx.send(f"⛔ **{member.name}** has been banned.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"🔓 **{user.name}** has been unbanned.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Violating rules"):
    await member.kick(reason=reason)
    await ctx.send(f"🚨 **{member.name}** has been kicked.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member = None, minutes: int = 10):
    if member is None:
        await ctx.send("❌ Mention a user! Example: `.mute @user 10`", delete_after=5)
        return
    try:
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=f"Muted by {ctx.author.name}")
        await ctx.send(f"🔇 **{member.name}** is muted for `{minutes}` minutes!")
    except Exception as e:
        await ctx.send(f"❌ Cannot mute user. Error: {e}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("❌ Usage: `.unmute @user`", delete_after=5)
        return
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 **{member.name}** is unmuted!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    c.execute("INSERT INTO warns VALUES (?, ?)", (member.id, reason))
    conn.commit()
    await ctx.send(f"⚠️ **{member.name}** has been warned for: `{reason}`")

@bot.command()
async def warns(ctx, member: discord.Member):
    c.execute("SELECT reason FROM warns WHERE user_id = ?", (member.id,))
    res = c.fetchall()
    await ctx.send(f"📋 **{member.name}** has `{len(res)}` active warnings.")

@bot.command()
@commands.has_permissions(administrator=True)
async def clearwarns(ctx, member: discord.Member):
    c.execute("DELETE FROM warns WHERE user_id = ?", (member.id,))
    conn.commit()
    await ctx.send(f"🧹 Cleared all warnings for **{member.name}**")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted `{amount}` messages!", delete_after=2)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"⏱️ Slowmode set to `{seconds}` seconds.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lockdown(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel Locked Down!")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Channel Unlocked!")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def nuke(ctx):
    pos = ctx.channel.position
    nc = await ctx.channel.clone()
    await ctx.channel.delete()
    await nc.edit(position=pos)
    await nc.send("💥 Channel Nuked and recreated!")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def roleadd(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Added role **{role.name}** to {member.name}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def roleremove(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"❌ Removed role **{role.name}** from {member.name}")

# 💰 ECONOMY & GAMBLING
@bot.command()
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (member.id,))
    c.execute("SELECT wallet, bank FROM economy WHERE user_id = ?", (member.id,))
    w, b = c.fetchone()
    await ctx.send(f"💰 **{member.name}'s Balance:**\n💵 Wallet: `{w}` coins\n🏦 Bank: `{b}` coins")

@bot.command()
async def daily(ctx):
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (ctx.author.id,))
    c.execute("UPDATE economy SET wallet = wallet + 500 WHERE user_id = ?", (ctx.author.id,))
    conn.commit()
    await ctx.send("🎁 Claimed daily bonus of **500 coins**!")

@bot.command()
async def work(ctx):
    earn = random.randint(50, 200)
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (ctx.author.id,))
    c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earn, ctx.author.id))
    conn.commit()
    await ctx.send(f"💼 Worked hard and earned `{earn}` coins!")

@bot.command()
async def beg(ctx):
    earn = random.randint(10, 50)
    c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (ctx.author.id,))
    c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earn, ctx.author.id))
    conn.commit()
    await ctx.send(f"🥺 Someone gave you `{earn}` coins!")

@bot.command()
async def deposit(ctx, amount: int):
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amount:
        c.execute("UPDATE economy SET wallet = wallet - ?, bank = bank + ? WHERE user_id = ?", (amount, amount, ctx.author.id))
        conn.commit()
        await ctx.send(f"🏦 Deposited `{amount}` coins to bank!")

@bot.command()
async def withdraw(ctx, amount: int):
    c.execute("SELECT bank FROM economy WHERE user_id = ?", (ctx.author.id,))
    b = c.fetchone()[0]
    if b >= amount:
        c.execute("UPDATE economy SET bank = bank - ?, wallet = wallet + ? WHERE user_id = ?", (amount, amount, ctx.author.id))
        conn.commit()
        await ctx.send(f"🏧 Withdrew `{amount}` coins from bank!")

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amount:
        c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, ctx.author.id))
        c.execute("INSERT OR IGNORE INTO economy VALUES (?, 100, 0)", (member.id,))
        c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amount, member.id))
        conn.commit()
        await ctx.send(f"💸 Sent `{amount}` coins to {member.name}!")

@bot.command()
async def gamble(ctx, amount: int):
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (ctx.author.id,))
    w = c.fetchone()[0]
    if w >= amount:
        win = random.choice([True, False])
        if win:
            c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amount, ctx.author.id))
            await ctx.send(f"🎉 You WON `{amount}` coins!")
        else:
            c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, ctx.author.id))
            await ctx.send(f"🔻 You LOST `{amount}` coins!")
        conn.commit()

@bot.command()
async def slots(ctx, amount: int):
    emojis = ["🎰", "🍎", "💎", "7️⃣"]
    r = [random.choice(emojis) for _ in range(3)]
    await ctx.send(f"[{' | '.join(r)}]")

@bot.command()
async def coinflip(ctx, choice: str):
    res = random.choice(["heads", "tails"])
    await ctx.send(f"🪙 Result: **{res}** - {'Won!' if choice.lower() == res else 'Lost!'}")

@bot.command()
async def rob(ctx, member: discord.Member):
    c.execute("SELECT wallet FROM economy WHERE user_id = ?", (member.id,))
    row = c.fetchone()
    if row and row[0] > 50:
        stolen = random.randint(10, row[0])
        c.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (stolen, member.id))
        c.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (stolen, ctx.author.id))
        conn.commit()
        await ctx.send(f"🥷 Stole `{stolen}` coins from {member.name}!")
    else: 
        await ctx.send("❌ Target doesn't have enough cash to steal!")

# 📈 LEVELS & INFORMATION
@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (member.id,))
    r = c.fetchone() or (0, 1)
    await ctx.send(f"📊 **{member.name}** | Level: `{r[1]}` | XP: `{r[0]}/{r[1]*100}`")

@bot.command()
async def leaderboard(ctx):
    c.execute("SELECT user_id, level FROM levels ORDER BY level DESC LIMIT 5")
    top = c.fetchall()
    msg = "\n".join([f"{i+1}. <@{u[0]}> - Level {u[1]}" for i, u in enumerate(top)])
    await ctx.send(f"🏆 **Top 5 Level Leaderboard**\n{msg}")

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    await ctx.send(f"🏰 **{g.name}** | Members: `{g.member_count}` | Created: `{g.created_at.strftime('%Y-%m-%d')}`")

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"👤 **{member.name}** | ID: `{member.id}` | Joined: `{member.joined_at.strftime('%Y-%m-%d')}`")

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
async def roleinfo(ctx, role: discord.Role): 
    await ctx.send(f"🎭 **{role.name}** | ID: `{role.id}` | Color: `{role.color}`")

@bot.command()
async def channelinfo(ctx): 
    await ctx.send(f"📺 **{ctx.channel.name}** | ID: `{ctx.channel.id}`")

# 🎫 UTILITY & TICKETS
@bot.command()
async def ticket(ctx):
    ch = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}")
    await ch.set_permissions(ctx.guild.default_role, read_messages=False)
    await ch.set_permissions(ctx.author, read_messages=True)
    await ch.send(f"🎫 Support Ticket created for {ctx.author.mention}. Use `.closeticket` to close.")

@bot.command()
async def closeticket(ctx):
    if "ticket-" in ctx.channel.name: 
        await ctx.channel.delete()

@bot.command()
async def poll(ctx, *, question: str):
    msg = await ctx.send(f"📊 **POLL:** {question}")
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
    await ctx.send(embed=discord.Embed(description=text, color=0x00ffff))

# 🎉 FUN & UTILITIES
@bot.command()
async def eightball(ctx, *, question: str):
    ans = ["Yes", "No", "Definitely", "Ask again later", "Never"]
    await ctx.send(f"🎱 **Q:** {question}\n**A:** {random.choice(ans)}")

@bot.command()
async def roll(ctx, dice: str = "1d6"):
    await ctx.send(f"🎲 Rolled: `{random.randint(1, 6)}`")

@bot.command()
async def choose(ctx, *options):
    await ctx.send(f"🤔 Choice: `{random.choice(options)}`")

@bot.command()
async def calculator(ctx, expression: str):
    try: 
        await ctx.send(f"🧮 Result: `{eval(expression)}`")
    except Exception: 
        await ctx.send("❌ Invalid expression")

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, member: discord.Member, *, text: str):
    await member.send(f"📩 Direct Message from **{ctx.guild.name}**: {text}")
    await ctx.send("✅ Sent!")

# --- BOT LAUNCHER ---
async def main():
    keep_alive()
    async with bot:
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
