import discord
from discord.ext import commands
import aiosqlite
import random

class CoreSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "bot_database.db"

    # Dot Command Menu
    @commands.command(name="cmd", aliases=["help"])
    async def cmd(self, ctx):
        embed = discord.Embed(title="⚡ BOT COMMANDS LIST", color=discord.Color.blue())
        embed.add_field(name="🛡️ Admin", value="`.clear <num>` | `.kick @user` | `.ban @user`", inline=False)
        embed.add_field(name="🪙 Economy", value="`.daily` | `.bal`", inline=False)
        embed.add_field(name="⭐ Level", value="`.rank`", inline=False)
        embed.add_field(name="🎟️ Support", value="`.ticket` | `.close`", inline=False)
        await ctx.send(embed=embed)

    # Auto XP track
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (message.author.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    xp, level = row[0] + random.randint(5, 15), row[1]
                    if xp >= level * 100:
                        level += 1
                        await message.channel.send(f"🎉 {message.author.mention} Leveled up to **Level {level}**!")
                    await db.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (xp, level, message.author.id))
                else:
                    await db.execute("INSERT INTO users (user_id, xp, level, balance) VALUES (?, 10, 1, 100)", (message.author.id,))
                await db.commit()

    # Commands (.rank, .daily, .bal, .clear, .ticket, .close)
    @commands.command(name="rank")
    async def rank(self, ctx):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    await ctx.send(f"📊 **{ctx.author.name}** | Level: {row[1]} | XP: {row[0]}")

    @commands.command(name="daily")
    async def daily(self, ctx):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE users SET balance = balance + 500 WHERE user_id = ?", (ctx.author.id,))
            await db.commit()
            await ctx.send(f"🪙 {ctx.author.mention}, you collected 500 Daily Coins!")

    @commands.command(name="bal")
    async def bal(self, ctx):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (ctx.author.id,)) as cursor:
                row = await cursor.fetchone()
                coins = row[0] if row else 0
                await ctx.send(f"💰 Balance: {coins} Coins")

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Deleted {amount} messages.", delete_after=3)

    @commands.command(name="ticket")
    async def ticket(self, ctx):
        guild = ctx.guild
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), ctx.author: discord.PermissionOverwrite(read_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True)}
        ch = await guild.create_text_channel(f'ticket-{ctx.author.name}', overwrites=overwrites)
        await ch.send(f"🎟️ Ticket created for {ctx.author.mention}. Type `.close` to finish.")

    @commands.command(name="close")
    async def close(self, ctx):
        if "ticket-" in ctx.channel.name:
            await ctx.channel.delete()

async def setup(bot):
    await bot.add_cog(CoreSystem(bot))
