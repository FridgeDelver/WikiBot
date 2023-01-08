import os
import discord
from dotenv import load_dotenv
import requests
import json
import pandas as pd

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
df = pd.read_csv("language_codes.csv")
languages = {}

for i in range(len(df)):
    entry = df.iloc[i]
    languages[entry["Code"]] = entry["Language"]

class WikiBotClient(discord.Client):
    command_string = "!wiki"
    command_len = len(command_string)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.history = {}
        

    async def on_message(self, message):
        if message.content[:WikiBotClient.command_len] == WikiBotClient.command_string:
            print(f'New Query from {message.author}: {message.content}')
            author_id = message.author.id
            contents = message.content.split(" ", 1)

            if contents[0] == WikiBotClient.command_string:
                lang = "en"
            elif message.content[WikiBotClient.command_len] == "-":
                lang = contents[0][WikiBotClient.command_len + 1:]
                if lang not in languages:
                    await message.channel.send(f"<@{author_id}> Not a valid wikipedia language code.\n\
See 'https://en.wikipedia.org/wiki/List_of_Wikipedias' \
for a complete list of supported languages.")
            
            url = f"https://{lang}.wikipedia.org/w/api.php?origin=*"
            query = contents[1]
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
                    else:
                        await message.channel.send(f"<@{author_id}> Top result: {results[1][0]}\n{results[3][0]}")
            except:
                await message.channel.send(f"<@{author_id}> An unknown error occurred. Please try again later")

intents = discord.Intents.default()
intents.message_content = True

client = WikiBotClient(intents=intents)
client.run(TOKEN)