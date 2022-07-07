import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import psycopg2
import datetime
import sentry_sdk


# Set up Sentry error reporting
sentry_sdk.init(
    dsn="https://fb9dc7ef489e498186c0b3466ee934c7@o244019.ingest.sentry.io/6544328",
    traces_sample_rate=1.0
)


class PatchNotes(commands.Cog):
    # Run this function when the cog is loaded
    def __init__(self, bot):
        self.bot = bot
        self.getPatchNotes.start()

    # Run this function when the cog is unloaded
    def cog_unload(self):
        self.getPatchNotes.cancel()

    # Set up the connection to the database
    def connectToDatabase(self):
        connection = psycopg2.connect(database=os.getenv('POSTGRES_DATABASE'),
                                      user=os.getenv('POSTGRES_USER'),
                                      password=os.getenv('POSTGRES_PASSWORD'),
                                      host=os.getenv('POSTGRES_HOST'),
                                      port=os.getenv('POSTGRES_PORT'))
        return connection

    # Run this loop every 15 minutes
    @tasks.loop(seconds=900.0)
    async def getPatchNotes(self):
        await self.bot.wait_until_ready()
        load_dotenv()  # Load environment variables
        feed_page = requests.get(
            'https://www.escapefromtarkov.com/news/page/1')  # Get the feed page
        feed_soup = BeautifulSoup(feed_page.text, 'html.parser')
        # Get all the container elements
        feed_elements = feed_soup.find_all('div', class_='container')
        connection = self.connectToDatabase()  # Connect to database
        cursor = connection.cursor()  # Get database cursor
        link_elements = feed_elements[1].find_all('a')
        for link_element in link_elements:
            # If the element is a news item
            if '/news/id/' in link_element['href']:
                if "patch" in link_element.text.lower() or "update" in link_element.text.lower() or "hotfix" in link_element.text.lower() or "bugfix" in link_element.text.lower():  # Find updates that we care about
                    url = 'https://www.escapefromtarkov.com' + \
                        link_element['href']  # Generate a link to the update
                    # If we have already processed the update, skip it
                    cursor.execute(
                        "SELECT id FROM patchnotes WHERE patch_id = %s", (link_element['href'],))  # Get a list of updates from the database to see if we already have processed it
                    rows = cursor.rowcount
                    if rows > 0:
                        link = link_element['href']
                        print(f'Skipped patch: {link}')
                        pass
                    else:  # If we haven't processed the update, add it to the database
                        date = datetime.datetime.now()
                        cursor.execute(
                            "INSERT INTO patchnotes (patch_id, url, date) VALUES (%s, %s, %s)", (link_element['href'], url, date,))
                        connection.commit()  # Write changes to database
                        link = link_element['href']
                        print(f'Added patch: {link}')
                        # Get the content of the update
                        notes_page = requests.get(url)
                        notes_soup = BeautifulSoup(
                            notes_page.content, 'html.parser')
                        notes_elements = notes_soup.find(
                            "div", class_="article")  # Get the content of the patch note
                        notes_strings = [notes_elements.text[index: index + 1500]
                                         for index in range(0, len(notes_elements.text), 1500)]  # Limit the content of the update to 1500 characters
                        notes = notes_strings[0] + '...'
                        embed = discord.Embed(title=link_element.text, url=url,
                                              description=notes, color=discord.Color.greyple())  # Generate the Discord embed
                        embed.set_thumbnail(
                            url='https://web-store.escapefromtarkov.com/themes/eft/images/bs_logo.png')
                        embed.set_image(
                            url='https://web-store.escapefromtarkov.com/themes/eft/images/logo.png')
                        cursor.execute("SELECT channel_id FROM channels")
                        rows = cursor.fetchall()
                        for row in rows:
                            try:
                                channel = self.bot.get_channel(int(row[0]))
                                await channel.send(embed=embed)
                                link = link_element['href']
                                print(
                                    f'Sent {link} to channel: {str(row[0])}')
                            except:
                                print(
                                    f'Error sending message to channel: {str(row[0])}')
                                pass
        cursor.close()  # Close cursor
        connection.close()  # Close connection to database


def setup(bot):
    try:
        bot.add_cog(PatchNotes(bot))
    except:
        sentry_sdk.capture_exception()
