import os
import asyncio
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# Web Server (Keep Alive)
app = Flask('')

@app.route('/')
def home():
    return "Security Bot is Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Security Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🛡️ Security Bot Online as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name=".cmd | Security Guard"))

# Help Command
@bot.command()
async def cmd(ctx):
    embed = discord.Embed(title="🛡️ Server Security & Moderation", color=0xff0000)
    embed.add_field(name="🧹 `.clear <amount>`", value="Bulk delete messages (e.g. `.clear 10`)", inline=False)
    embed.add_field(name="🔨 `.kick <user> [reason]`", value="Kick a member from server", inline=False)
    embed.add_field(name="⛔ `.ban <user> [reason]`", value="Ban a member from server", inline=False)
    embed.add_field(name="🔓 `.unban <user_id>`", value="Unban a user using ID", inline=False)
    embed.add_field(name="🔇 `.mute <user>`", value="Timeout/Mute a member (10 mins)", inline=False)
    await ctx.send(embed=embed)

# 1. Clear Messages
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted `{amount}` messages!", delete_after=3)

# 2. Kick Member
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"🚨 **{member.name}** has been kicked. Reason: {reason}")

# 3. Ban Member
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"⛔ **{member.name}** has been banned. Reason: {reason}")

# 4. Mute/Timeout (10 Minutes)
@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member):
    await member.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=10))
    await ctx.send(f"🔇 **{member.name}** has been muted for 10 minutes.")

async def main():
    keep_alive()
    async with bot:
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
