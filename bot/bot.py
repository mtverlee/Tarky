import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import sentry_sdk
import psycopg2
import datetime
import requests
from bs4 import BeautifulSoup


# Set up Sentry error reporting
sentry_sdk.init(
    dsn="https://fb9dc7ef489e498186c0b3466ee934c7@o244019.ingest.sentry.io/6544328",
    traces_sample_rate=1.0
)


# Create a new Discord client
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="/", intents=intents)


# Set up the connection to the database
def connectToDatabase():
    connection = psycopg2.connect(database=os.getenv('POSTGRES_DATABASE'),
                                  user=os.getenv('POSTGRES_USER'),
                                  password=os.getenv('POSTGRES_PASSWORD'),
                                  host=os.getenv('POSTGRES_HOST'),
                                  port=os.getenv('POSTGRES_PORT'))
    return connection


# When the bot is ready, run this function
@bot.event
async def on_ready():
    print("Bot: ", f'{bot.user}')
    # Set the bot's activity
    await bot.change_presence(activity=discord.Game(name='Watching for patch notes!'))


# When the bot joins a server, run this function
@bot.event
async def on_guild_join(guild):
    connection = connectToDatabase()  # Connect to database
    guild_string = str(guild.id)
    date = datetime.datetime.now()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT guild_id FROM guilds WHERE guild_id = %s", (guild_string,))  # Look to see if the guild we're joining is already in the database
    rows = cursor.rowcount
    if rows > 0:
        cursor.close()
        connection.close()
        # If the guild is already in the database, skip it and notify the user
        print(f'Skipped guild: {guild.name} ({guild.id})')
    else:
        cursor.execute("INSERT INTO guilds (guild_id, name, date) VALUES (%s, %s, %s)",
                       (guild.id, guild.name, date))
        connection.commit()
        cursor.close()
        connection.close()
        # If the guild is not in the database, add it and notify the user
        print(f'Joined a new guild: {guild.name} ({guild.id})')


# When the bot leaves a server, run this function
@bot.event
async def on_guild_remove(guild):
    connection = connectToDatabase()  # Connect to database
    guild_string = str(guild.id)
    date = datetime.datetime.now()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT guild_id FROM guilds WHERE guild_id = %s", (guild_string,))  # Look to see if the guild we're leaving is already in the database
    rows = cursor.rowcount
    if rows > 0:
        cursor.execute("DELETE FROM guilds WHERE guild_id = %s",
                       (guild_string,))
        connection.commit()
        cursor.execute("DELETE FROM channels WHERE guild_id = %s",
                       (guild_string,))
        connection.commit()
        cursor.close()
        connection.close()
        # If the guild is in the database, remove it and corresponding channels, then notify the user
        print(f'Removed guild: {guild.name} ({guild.id})')
    else:
        cursor.close()
        connection.close()
        # If the guild is not in the database, skip it and notify the user
        print(f'Skipped removing guild: {guild.name} ({guild.id})')


# Set up add channel command
@bot.slash_command(name="tarkyadd", description="Add a channel to the database")
async def tarkyadd(ctx, channel):
    guild = int(ctx.guild.id)
    connection = connectToDatabase()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM channels WHERE channel_id = %s", (channel,))  # Get a list of channels from the database to see if we already have added it
    rows = cursor.rowcount
    if rows > 0:
        # If we already added the channel, tell the user
        print('Skipped adding channel: ', channel)
        await ctx.respond("Channel already added!")
    else:
        date = datetime.datetime.now()
        # If we haven't added the channel, add it to the database
        cursor.execute("INSERT INTO channels (channel_id, guild_id, date) VALUES (%s, %s, %s)",
                       (int(channel), guild, date))
        connection.commit()
        cursor.close()
        connection.close()
        # Tell the user the channel was added'
        new_channel = bot.get_channel(int(channel))
        print('Added channel: ', channel)
        await new_channel.send("This channel will now get patch notes from Escape from Tarkov!")
        await ctx.respond(f'Added channel {channel} to the list of channels to watch for patch notes!')


# Set up add channel command
@bot.slash_command(name="tarkyremove", description="Remove a channel from the database")
async def tarkyremove(ctx, channel):
    connection = connectToDatabase()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM channels WHERE channel_id = %s", (channel,))  # Get a list of channels from the database to see if we already have added it
    rows = cursor.rowcount
    if rows == 0:
        # If we can't find the channel, tell the user
        print('Skipped removing channel: ', channel)
        await ctx.respond("Channel not found!")
    else:
        # If we have added the channel, remove it from the database
        cursor.execute("DELETE FROM channels WHERE channel_id = %s",
                       (channel,))
        connection.commit()
        cursor.close()
        connection.close()
        # Tell the user the channel was removed
        print('Removed channel: ', channel)
        await ctx.respond(f'Removed channel {channel} from the list of channels to watch for patch notes!')


# Set up last patch command
@bot.slash_command(name="tarkylast", description="Get the last patch notes")
async def tarkylast(ctx):
    connection = connectToDatabase()  # Connect to database
    cursor = connection.cursor()
    cursor.execute(
        "SELECT patch_id FROM patchnotes ORDER BY id DESC LIMIT 1")
    rows = cursor.fetchone()  # Get the last patch ID
    url = 'https://www.escapefromtarkov.com' + rows[0]
    notes_page = requests.get(url)
    notes_soup = BeautifulSoup(
        notes_page.content, 'html.parser')
    notes_elements = notes_soup.find(
        "div", class_="article")  # Get the content of the patch note
    title_page = requests.get(url)
    title_soup = BeautifulSoup(
        title_page.content, 'html.parser')
    title_element = title_soup.find("h1")  # Get the title of the patch note
    notes_strings = [notes_elements.text[index: index + 1500]
                     for index in range(0, len(notes_elements.text), 1500)]  # Limit the content of the update to 1500 characters
    notes = notes_strings[0] + '...'
    embed = discord.Embed(title=title_element.text, url=url,
                          description=notes, color=discord.Color.dark_gray())  # Generate the Discord embed
    embed.set_thumbnail(
        url='https://web-store.escapefromtarkov.com/themes/eft/images/bs_logo.png')
    embed.set_image(
        url='https://web-store.escapefromtarkov.com/themes/eft/images/logo.png')
    print(f'Sent {ctx.author.name} last patch notes: {title_element}')
    await ctx.respond(embed=embed)  # Send the embed back to the user


# Set up news command
@ bot.slash_command(name="tarkynews", description="Get the Escape from Tarkov news")
async def tarkynews(ctx):
    newsembed = discord.Embed(title='News', url='https://www.escapefromtarkov.com/news',
                              description='Find information about Escape from Tarkov here.', color=discord.Color.dark_gray())  # Generate Discord embed
    newsembed.set_thumbnail(
        url='https://web-store.escapefromtarkov.com/themes/eft/images/bs_logo.png')
    newsembed.set_image(
        url='https://web-store.escapefromtarkov.com/themes/eft/images/logo.png')
    await ctx.respond(embed=newsembed)  # Send the embed back to the user

# Run bot
try:
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.load_extension('cogs.patchnotes')
    bot.run(TOKEN)
except:
    sentry_sdk.capture_exception()
