import discord
from discord.ext import commands
import aiosqlite
import os
import re
from dotenv import load_dotenv

# Configuration
load_dotenv()
TOKEN = os.getenv('bot_token')
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

    # Check if message starts with "based" or "cringe" (case-insensitive), optionally preceded by a mention
    content = message.content.strip()
    match = re.match(r'^(?:<@!?\d+>\s+)?(based|cringe)', content, re.IGNORECASE)

    if match:
        keyword = match.group(1).lower()
        if keyword == "based":
            await handle_based_event(message)
        elif keyword == "cringe":
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
    # Updated to allow optional mention at start
    match = re.search(r'^(?:<@!?\d+>\s+)?based(?:\s+and)?\s+(.*)', message.content.strip(), re.IGNORECASE)
    new_pill = match.group(1).strip() if match else None
    
    # Remove mentions from the pill text
    if new_pill:
        new_pill = re.sub(r'<@!?\d+>', '', new_pill).strip()

    # Update Database
    async with aiosqlite.connect(DB_NAME) as db:
        # Update Count
        await db.execute('''
            INSERT INTO users (user_id, count) VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET count = count + 1
        ''', (target_user.id,))
        
        # Insert Pill if exists (and is not empty after stripping mentions)
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

        # Get Pills (All)
        cursor = await db.execute('SELECT pill_text FROM pills WHERE user_id = ? ORDER BY id DESC', (user.id,))
        pills = await cursor.fetchall()
        
    valid_pills = [p[0] for p in pills if p[0] and p[0].strip()]
    
    if valid_pills:
        pill_list = "\n".join([f"- {p}" for p in valid_pills])
        # Truncate if too long (Discord limit is ~1024 per field)
        if len(pill_list) > 1000:
            pill_list = pill_list[:1000] + "...\n*(truncated)*"
    else:
        pill_list = "No pills yet."
    
    embed = discord.Embed(title=f"Based Profile: {user.display_name}", color=0x00ff00)
    embed.add_field(name="Based Count", value=str(count), inline=False)
    embed.add_field(name="Cringe Count", value=str(cringe_count), inline=False)
    embed.add_field(name="Pills", value=pill_list, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    """Shows the top 5 based users."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT user_id, count, cringe_count FROM users ORDER BY count DESC LIMIT 5')
        rows = await cursor.fetchall()

    if not rows:
        await ctx.send("No one is based yet.")
        return

    embed = discord.Embed(title="🏆 Based Leaderboard", color=0xFFD700)
    
    for idx, (user_id, count, cringe_count) in enumerate(rows, 1):
        # Fetch user object to get name
        user = ctx.guild.get_member(user_id)
        name = user.display_name if user else f"User {user_id}"
        
        # Get all pills
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute('SELECT pill_text FROM pills WHERE user_id = ? ORDER BY id DESC', (user_id,))
            pill_rows = await cursor.fetchall()
            pills = [row[0] for row in pill_rows if row[0] and row[0].strip()]

        # Build Field Value
        value = f"**Based:** {count} | **Cringe:** {cringe_count}"
        
        if pills:
            pill_str = "\n".join([f"💊 *{pill}*" for pill in pills])
            # Truncate if too long (Discord limit is 1024, keeping it safe at 900)
            if len(pill_str) > 900:
                pill_str = pill_str[:900] + "...\n*(truncated)*"
            value += f"\n{pill_str}"
        
        embed.add_field(name=f"#{idx} {name}", value=value, inline=False)

    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    """Shows help information about all commands and how to use the bot."""
    embed = discord.Embed(
        title="📖 Based Count Bot - Help",
        description="Track based and cringe counts, collect pills, and compete on the leaderboard!",
        color=0x3498db
    )
    
    # Commands Section
    embed.add_field(
        name="📋 Commands",
        value=(
            "**!mybased** - View your based/cringe count and pills\n"
            "**!checkbased @user** - Check another user's stats\n"
            "**!leaderboard** - View the top 5 most based users\n"
            "**!help** - Show this help message"
        ),
        inline=False
    )
    
    # Usage Section
    embed.add_field(
        name="✅ How to Give Based/Cringe",
        value=(
            "**Reply** to a message with \"based\" or \"cringe\"\n"
            "**Mention** a user: `@User based` or `@User cringe`"
        ),
        inline=False
    )
    
    # Pills Section
    embed.add_field(
        name="💊 How to Add Pills",
        value=(
            "Reply with \"based and [text]\"\n"
            "Example: `based and logic pilled`"
        ),
        inline=False
    )
    
    # Rules Section
    embed.add_field(
        name="⚠️ Rules",
        value=(
            "• You cannot base/cringe yourself\n"
            "• Bots cannot receive based/cringe counts"
        ),
        inline=False
    )
    
    embed.set_footer(text="Based Count Bot | Inspired by r/basedcount_bot")
    
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
