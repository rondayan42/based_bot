import discord
from discord.ext import commands
import aiosqlite
import os
import re

# Configuration
TOKEN = 'YOUR_DISCORD_BOT_TOKEN_HERE'
DB_NAME = 'based_count.db'

# Setup Intents (Required for reading message content)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def init_db():
    """Initializes the SQLite database."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS pills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pill_text TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        await db.commit()

@bot.event
async def on_ready():
    await init_db()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('BasedCount database initialized.')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if message starts with "based" (case-insensitive)
    content_lower = message.content.lower().strip()
    if content_lower.startswith("based"):
        await handle_based_event(message)

    # Process actual commands (like !profile)
    await bot.process_commands(message)

async def handle_based_event(message):
    target_user = None

    # 1. Check if it is a Reply
    if message.reference and message.reference.resolved:
        if isinstance(message.reference.resolved, discord.Message):
            target_user = message.reference.resolved.author

    # 2. If not a reply, check if a user is Mentioned
    elif message.mentions:
        target_user = message.mentions[0]

    # If no target found, ignore
    if not target_user:
        return

    # Prevent self-basing
    if target_user.id == message.author.id:
        await message.channel.send(f"{message.author.mention} You cannot base yourself! Cringe.")
        return

    # Prevent basing bots
    if target_user.bot:
        await message.channel.send("Bots cannot be based.")
        return

    # Extract "Pill" (text after 'based' and optional 'and')
    # Regex looks for "based", optionally "and", then captures the rest
    match = re.search(r'^based(?:\s+and)?\s+(.*)', message.content, re.IGNORECASE)
    new_pill = match.group(1).strip() if match else None

    # Update Database
    async with aiosqlite.connect(DB_NAME) as db:
        # Update Count
        await db.execute('''
            INSERT INTO users (user_id, count) VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET count = count + 1
        ''', (target_user.id,))
        
        # Insert Pill if exists
        if new_pill:
            # Clean the pill text slightly to prevent massive spam
            clean_pill = new_pill[:100] # Limit length
            await db.execute('INSERT INTO pills (user_id, pill_text) VALUES (?, ?)', (target_user.id, clean_pill))
        
        await db.commit()
        
        # Get new count
        cursor = await db.execute('SELECT count FROM users WHERE user_id = ?', (target_user.id,))
        row = await cursor.fetchone()
        new_count = row[0]

    # Send Response
    response = f"Based! {target_user.mention}'s based count is now **{new_count}**."
    if new_pill:
        response += f"\n💊 Pill added: *{new_pill}*"
    
    await message.channel.send(response)

@bot.command(name="mybased")
async def my_profile(ctx):
    """Shows your based count and recent pills."""
    user = ctx.author
    await show_profile(ctx, user)

@bot.command(name="checkbased")
async def check_profile(ctx, member: discord.Member):
    """Checks another user's based count."""
    await show_profile(ctx, member)

async def show_profile(ctx, user):
    async with aiosqlite.connect(DB_NAME) as db:
        # Get Count
        cursor = await db.execute('SELECT count FROM users WHERE user_id = ?', (user.id,))
        row = await cursor.fetchone()
        
        if not row:
            await ctx.send(f"{user.display_name} has no based count yet.")
            return

        count = row[0]

        # Get Pills (Limit to last 5)
        cursor = await db.execute('SELECT pill_text FROM pills WHERE user_id = ? ORDER BY id DESC LIMIT 5', (user.id,))
        pills = await cursor.fetchall()
        
    pill_list = "\n".join([f"- {p[0]}" for p in pills]) if pills else "No pills yet."
    
    embed = discord.Embed(title=f"Based Profile: {user.display_name}", color=0x00ff00)
    embed.add_field(name="Based Count", value=str(count), inline=False)
    embed.add_field(name="Recent Pills", value=pill_list, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    """Shows the top 5 based users."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT user_id, count FROM users ORDER BY count DESC LIMIT 5')
        rows = await cursor.fetchall()

    if not rows:
        await ctx.send("No one is based yet.")
        return

    description = ""
    for idx, (user_id, count) in enumerate(rows, 1):
        # Fetch user object to get name
        user = ctx.guild.get_member(user_id)
        name = user.display_name if user else f"User {user_id}"
        description += f"**{idx}.** {name} - **{count}**\n"

    embed = discord.Embed(title="Based Leaderboard", description=description, color=0xFFD700)
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
import discord
from discord.ext import commands
import aiosqlite
import os
import re

# Configuration
TOKEN = 'YOUR_DISCORD_BOT_TOKEN_HERE'
DB_NAME = 'based_count.db'

# Setup Intents (Required for reading message content)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def init_db():
    """Initializes the SQLite database."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                count INTEGER DEFAULT 0,
                cringe_count INTEGER DEFAULT 0
            )
        ''')
        try:
            await db.execute('ALTER TABLE users ADD COLUMN cringe_count INTEGER DEFAULT 0')
        except Exception:
            pass

        await db.execute('''
            CREATE TABLE IF NOT EXISTS pills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pill_text TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        await db.commit()

@bot.event
async def on_ready():
    await init_db()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('BasedCount database initialized.')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if message starts with "based" (case-insensitive)
    content_lower = message.content.lower().strip()
    if content_lower.startswith("based"):
        await handle_based_event(message)
    elif content_lower.startswith("cringe"):
        await handle_cringe_event(message)

    # Process actual commands (like !profile)
    await bot.process_commands(message)

async def handle_based_event(message):
    target_user = None

    # 1. Check if it is a Reply
    if message.reference and message.reference.resolved:
        if isinstance(message.reference.resolved, discord.Message):
            target_user = message.reference.resolved.author

    # 2. If not a reply, check if a user is Mentioned
    elif message.mentions:
        target_user = message.mentions[0]

    # If no target found, ignore
    if not target_user:
        return

    # Prevent self-basing
    if target_user.id == message.author.id:
        await message.channel.send(f"{message.author.mention} You cannot base yourself! Cringe.")
        return

    # Prevent basing bots
    if target_user.bot:
        await message.channel.send("Bots cannot be based.")
        return

    # Extract "Pill" (text after 'based' and optional 'and')
    # Regex looks for "based", optionally "and", then captures the rest
    match = re.search(r'^based(?:\s+and)?\s+(.*)', message.content, re.IGNORECASE)
    new_pill = match.group(1).strip() if match else None

    # Update Database
    async with aiosqlite.connect(DB_NAME) as db:
        # Update Count
        await db.execute('''
            INSERT INTO users (user_id, count) VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET count = count + 1
        ''', (target_user.id,))
        
        # Insert Pill if exists
        if new_pill:
            # Clean the pill text slightly to prevent massive spam
            clean_pill = new_pill[:100] # Limit length
            await db.execute('INSERT INTO pills (user_id, pill_text) VALUES (?, ?)', (target_user.id, clean_pill))
        
        await db.commit()
        
        # Get new count
        cursor = await db.execute('SELECT count FROM users WHERE user_id = ?', (target_user.id,))
        row = await cursor.fetchone()
        new_count = row[0]

    # Send Response
    response = f"Based! {target_user.mention}'s based count is now **{new_count}**."
    if new_pill:
        response += f"\n💊 Pill added: *{new_pill}*"
    
    await message.channel.send(response)

async def handle_cringe_event(message):
    target_user = None

    # 1. Check if it is a Reply
    if message.reference and message.reference.resolved:
        if isinstance(message.reference.resolved, discord.Message):
            target_user = message.reference.resolved.author

    # 2. If not a reply, check if a user is Mentioned
    elif message.mentions:
        target_user = message.mentions[0]

    # If no target found, ignore
    if not target_user:
        return

    # Prevent self-cringe
    if target_user.id == message.author.id:
        await message.channel.send(f"{message.author.mention} You cannot call yourself cringe! That's... actually cringe.")
        return

    # Prevent bots
    if target_user.bot:
        await message.channel.send("Bots cannot be cringe.")
        return

    # Update Database
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (user_id, count, cringe_count) VALUES (?, 0, 1)
            ON CONFLICT(user_id) DO UPDATE SET cringe_count = cringe_count + 1
        ''', (target_user.id,))
        await db.commit()
        
        cursor = await db.execute('SELECT cringe_count FROM users WHERE user_id = ?', (target_user.id,))
        row = await cursor.fetchone()
        new_count = row[0]

    await message.channel.send(f"Cringe! {target_user.mention}'s cringe count is now **{new_count}**.")

@bot.command(name="mybased")
async def my_profile(ctx):
    """Shows your based count and recent pills."""
    user = ctx.author
    await show_profile(ctx, user)

@bot.command(name="checkbased")
async def check_profile(ctx, member: discord.Member):
    """Checks another user's based count."""
    await show_profile(ctx, member)

async def show_profile(ctx, user):
    async with aiosqlite.connect(DB_NAME) as db:
        # Get Count
        cursor = await db.execute('SELECT count, cringe_count FROM users WHERE user_id = ?', (user.id,))
        row = await cursor.fetchone()
        
        if not row:
            await ctx.send(f"{user.display_name} has no based or cringe count yet.")
            return

        count = row[0]
        cringe_count = row[1]

        # Get Pills (Limit to last 5)
        cursor = await db.execute('SELECT pill_text FROM pills WHERE user_id = ? ORDER BY id DESC LIMIT 5', (user.id,))
        pills = await cursor.fetchall()
        
    pill_list = "\n".join([f"- {p[0]}" for p in pills]) if pills else "No pills yet."
    
    embed = discord.Embed(title=f"Based Profile: {user.display_name}", color=0x00ff00)
    embed.add_field(name="Based Count", value=str(count), inline=False)
    embed.add_field(name="Cringe Count", value=str(cringe_count), inline=False)
    embed.add_field(name="Recent Pills", value=pill_list, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    """Shows the top 5 based users."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT user_id, count FROM users ORDER BY count DESC LIMIT 5')
        rows = await cursor.fetchall()

    if not rows:
        await ctx.send("No one is based yet.")
        return

    description = ""
    for idx, (user_id, count) in enumerate(rows, 1):
        # Fetch user object to get name
        user = ctx.guild.get_member(user_id)
        name = user.display_name if user else f"User {user_id}"
        description += f"**{idx}.** {name} - **{count}**\n"

    embed = discord.Embed(title="Based Leaderboard", description=description, color=0xFFD700)
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
