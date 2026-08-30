import os
import asyncio
import discord
from discord.ext import commands
import aiosqlite
from flask import Flask
from threading import Thread

# Web Server (For Render)
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

async def init_db():
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                balance INTEGER DEFAULT 0
            )
        """)
        await db.commit()

@bot.event
async def on_ready():
    await init_db()
    print(f'🚀 Logged in as {bot.user.name} | Active Prefix: .')
    await bot.change_presence(activity=discord.Game(name=".cmd | Dot Commands"))

async def load_extensions():
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    keep_alive()
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
