import os
import discord
from dotenv import load_dotenv
import requests
import json
import pandas as pd
import urllib.parse

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
df = pd.read_csv("language_codes.csv")
languages = {}

for i in range(len(df)):
    entry = df.iloc[i]
    languages[entry["Code"]] = entry["Language"]

class WikiBotClient(discord.Client):
    def __init__(self, intents, **kwargs):
        discord.Client.__init__(self, intents = intents)
        self.query_history = {}

    def generate_entry(author, guild, channel):
        return f"{author} {guild} {channel}"

    async def on_ready(self):
        print(f'Logged on as {self.user}!')    

    async def on_message(self, message):
        content = message.content.lower()
        if content[:5] == "!wiki":
            print(f'New Query from {message.author}: {content}')
            author_id = message.author.id
            message_components = content.split(" ", 1)

            if content == "!wikinext":
                entry = WikiBotClient.generate_entry(author_id, message.guild, message.channel.id)
                if entry not in self.query_history:
                    await message.channel.send(f"<@{author_id}> Sorry no previous query found try searching for it again")
                    return

                query = urllib.parse.unquote(self.query_history[entry][1])
                prev_url = self.query_history[entry][0].rsplit("=", 1)
                num = int(prev_url[1]) + 1
                url = f"{prev_url[0]}={num}"

            else:
                if message_components[0] == "!wiki":
                    lang = "en"
                elif content[5] == "-":
                    lang = message_components[0][6:]
                    if lang not in languages:
                        await message.channel.send(f"<@{author_id}> Not a valid wikipedia language code.\n\
See 'https://en.wikipedia.org/wiki/List_of_Wikipedias' \
for a complete list of supported languages.")
            
                url = f"https://{lang}.wikipedia.org/w/api.php?origin=*"
                query = urllib.parse.quote(message_components[1])
                num = 1
                parameters = {
                    "action": "opensearch",
                    "search": query,
                    "namespace": "0",
                    "format": "json",
                    "limit": str(num)
                }
                
                for param in parameters:
                    url += f"&{param}={parameters[param]}"

            try:
                response = requests.get(url)
                if (response.status_code != 200): 
                    await message.channel.send(f"<@{author_id}> An unknown error occurred. Please try again later")

                else:
                    if (response.url != url):
                        new_lang =  response.url.split(".")[0][8:]
                        await message.channel.send(f"The correct code for language '{languages[new_lang]}' is \
'{new_lang}' not '{lang}'")

                    results = json.loads(response.content)
                    if (len(results[1]) == 0):
                        await message.channel.send(f"<@{author_id}> No results found for '{query}'. \
Try refining your search terms")
                    elif (len(results[1]) < num):
                         await message.channel.send(f"<@{author_id}> No more results found for '{query}'. \
Try refining your search terms")
                    else:
                        message_details = WikiBotClient.generate_entry(author_id, message.guild, message.channel.id)
                        self.query_history[message_details] = [url, query]
                        await message.channel.send(f"<@{author_id}> Top result: {results[1][num - 1]}\n{results[3][num - 1]}")
            except Exception as e:
                print(e)
                await message.channel.send(f"<@{author_id}> An unknown error occurred. Please try again later")

intents = discord.Intents.default()
intents.message_content = True

client = WikiBotClient(intents)
client.run(TOKEN)