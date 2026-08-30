import os
import asyncio
import datetime
import re
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Ultra Security Bot Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

# Anti-Spam Memory Tracking
user_messages = {}

@bot.event
async def on_ready():
    print(f'🛡️ Security Bot Online: {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name=".cmd | Server Guard 🛡️"))

# --- AUTOMATIC SECURITY (Anti-Link & Anti-Spam) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Anti-Link System (Deletes unauthorized invite/external links)
    if not message.author.guild_permissions.administrator:
        link_regex = r"(https?://\S+|discord\.gg/\S+)"
        if re.search(link_regex, message.content):
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, Links are not allowed here!", delete_after=4)
            return

    # 2. Anti-Spam System (Timeouts user sending 5+ messages in 4 seconds)
    user_id = message.author.id
    current_time = datetime.datetime.now().timestamp()
    
    if user_id not in user_messages:
        user_messages[user_id] = []
    
    user_messages[user_id].append(current_time)
    user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < 4]

    if len(user_messages[user_id]) > 5 and not message.author.guild_permissions.administrator:
        user_messages[user_id] = []
        try:
            await message.author.timeout(datetime.timedelta(minutes=5), reason="Anti-Spam Triggered")
            await message.channel.send(f"🔇 {message.author.mention} was muted for 5 minutes (Spamming).", delete_after=5)
        except Exception:
            pass

    await bot.process_commands(message)

# --- COMMANDS MENU ---
@bot.command()
async def cmd(ctx):
    embed = discord.Embed(title="🛡️ Ultra Security & Moderation Suite", color=0xff0000)
    embed.add_field(name="🚨 Emergency Controls", value="`.lockdown` - Lock down current channel\n`.unlock` - Unlock current channel", inline=False)
    embed.add_field(name="🧹 Cleanup & Moderation", value="`.clear <amount>` - Bulk delete messages\n`.warn <user> <reason>` - Send official warning\n`.mute <user> <mins>` - Timeout a member", inline=False)
    embed.add_field(name="⛔ Ban/Kick System", value="`.kick <user> [reason]` - Kick member\n`.ban <user> [reason]` - Ban member\n`.unban <user_id>` - Unban using User ID", inline=False)
    embed.add_field(name="⚙️ Server Utilities", value="`.botstatus` - View bot latency & status\n`.userinfo <user>` - Check account creation date & details", inline=False)
    embed.set_footer(text="Anti-Link & Anti-Spam are automatically ACTIVE.")
    await ctx.send(embed=embed)

# --- EMERGENCY COMMANDS ---
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lockdown(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 **Channel Locked Down!** Members cannot send messages.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 **Channel Unlocked!**")

# --- MODERATION & PUNISHMENT COMMANDS ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted `{amount}` messages!", delete_after=3)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason specified"):
    try:
        await member.send(f"⚠️ **Warning from {ctx.guild.name}:** {reason}")
    except Exception:
        pass
    await ctx.send(f"⚠️ **{member.name}** has been warned. Reason: `{reason}`")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int = 10):
    await member.timeout(datetime.timedelta(minutes=minutes))
    await ctx.send(f"🔇 **{member.name}** muted for `{minutes}` minutes.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Violating rules"):
    await member.kick(reason=reason)
    await ctx.send(f"🚨 **{member.name}** has been kicked.")

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

# --- UTILITIES ---
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 User Details - {member.name}", color=0x00ff00)
    embed.add_field(name="User ID", value=member.id, inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%b %d, %Y"), inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%b %d, %Y"), inline=True)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

async def main():
    keep_alive()
    async with bot:
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
