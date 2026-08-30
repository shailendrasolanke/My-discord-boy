import os
import asyncio
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# Flask Web Server
app = Flask('')

@app.route('/')
def home():
    return "Bot is Live!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f'🚀 Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name=".cmd | Online"))

@bot.command()
async def cmd(ctx):
    await ctx.send("✅ Bot working correctly!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")

async def main():
    keep_alive()
    async with bot:
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
