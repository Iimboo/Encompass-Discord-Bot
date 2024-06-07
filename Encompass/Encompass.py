from discord.ext import commands, tasks
import discord
import yt_dlp as youtube_dl
import pytz
from datetime import datetime
from dataclasses import dataclass
import random
import asyncio
import re
from googleapiclient.discovery import build


################################## SET UP ###############################################
BOT_TOKEN = "ENTER BOT TOKEN HERE"
CHANNEL_ID = "ENTER CHANNEL ID HERE"
WATER_REMINDER_MINUTES = 30
YOUTUBE_API_KEY = "ENTER YOUTUBE API KEY HERE"

bot = commands.Bot(command_prefix ="/", intents=discord.Intents.all())
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


@bot.event #decorator that takes the function "on_ready"
async def on_ready():
    welcome_messages = [
    "I'm ALIVEEEEEEEEEEE!",
    "Greetings, fellow human! 🤖 I’m here and ready to serve!",
    "Guess who just woke up from a digital nap? It’s me! 🎉",
    "Hey there! I promise not to malfunction too often. 😉",
]
    print(random.choice(welcome_messages))
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(random.choice(welcome_messages))
###############################################################################################

############### Water Reminder ########################
@dataclass
class drinksession:
    is_active: bool = False

drinksession = drinksession()

@tasks.loop(minutes = WATER_REMINDER_MINUTES) #water_reminder_minutes is a placeholder, in function drink, change_interval will be the actual interval
async def water_reminder():
    if water_reminder.current_loop == 0:
        return
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("Time to drink water!")

@bot.command()
async def drink(ctx, x:int):
    if drinksession.is_active:
        await ctx.send(f"Another drink reminder is currently active!")
        return
    drinksession.is_active = True
    water_reminder.change_interval(minutes = x)
    water_reminder.start()
    await ctx.send(f"Water reminder started! You will be reminded every {x} minutes.")
    
@bot.command()
async def stopdrink(ctx):
    if not drinksession.is_active:
        await ctx.send(f"No drink reminders currently active. Start one!")
    drinksession.is_active = False
    water_reminder.stop()
    await ctx.send(f"Water reminder stopped. Don't forget to hydrate yourself!")
    
###############################################################################

######################## MUSIC BOT ############################################

@dataclass
class MusicQueue:
    def __init__(self):
        self.queue =[]
    
    #Adding functions of a queue
    async def enqueue(self,url:str):
        title = await self.get_title(url)
        self.queue.append({"url": url, "title": title})
    
    async def get_title(self, url: str) -> str:
        video_id = await self.search_youtube(url)
        if not video_id:
            raise ValueError("Could not find a video for the provided URL or query.")
        return await self.get_video_title(video_id)
    
    async def search_youtube(self, query: str) -> str:
        request = youtube.search().list(
            q=query,
            part="id",
            maxResults=1,
            type="video"
        )
        response = request.execute()
        if response['items']:
            return response['items'][0]['id']['videoId']
        return None
    
    async def get_video_title(self, video_id: str) -> str:
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        if response['items']:
            return response['items'][0]['snippet']['title']
        return "Unknown Title"
    
    def dequeue(self):
        if not self.is_empty():
            return self.queue.pop(0)
    
    def peek(self):
        if not self.is_empty():
            return self.queue[0]
        return None
        
    def is_empty(self):
        return (len(self.queue) == 0)
    
    def clear(self):
        self.queue = []
        
    async def printqueue(self,ctx):
        counter = 1
        if not self.is_empty():
            await ctx.send("Songs in Queue\n")
            for i in self.queue:
                await ctx.send(f"{counter}: {i['title']}")
                counter +=1
        else:
            await ctx.send("The queue is empty.")

Music_Queue = MusicQueue()

ffmpeg_path = "C:/ffmpeg/bin/ffmpeg.exe" 

ytdl_format_options = {
    'format': 'bestaudio[ext=webm]/bestaudio[ext=mp4]/best', #Chooses the best audio quality
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s', # % indicates a placeholder and s is a format specifier, telling python to treat the value as a string
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # binds outgoing connections to ipv4 addresses, 0.0.0.0 is a wildcard address
}

ffmpeg_options = {
    'executable': ffmpeg_path,
    'options': '-vn -buffer_size 10240k' #Tells ffmpeg to skip video stream and process only the audio stream
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options) #YoutubeDL is a class within discord.py, passes in formatting options for the youtube vid

class YTDLSource(discord.PCMVolumeTransformer): #discord.PCMVolumeTransformer is a superclass here, making YTDL the subclass, hence super init allows us to use the init in the superclass
    def __init__(self, source, *, data, volume=0.5): 
        # * means that when calling the function, any variable after * must be specified as keyword arguments: e.g. my_function(c=3) instead of my_function(3)
        
        super().__init__(source, volume) #Calling the init function from the superclass

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False): #cls is similar to ctx, just context arguments
        loop = loop or asyncio.get_event_loop() #Gets specified event loop or gets current event loop if event loop is not specified by the user
        
        #run_in_executor used when you want to run a blocking function without blocking the main event loop, uses default executor since "None" is used
        #lambda is used because run_in_executor expects a callable function as it's argument, if you use extract_info directly, you end up passing the returned value instead.
        #when the video is streamable (true), set download to false as there is no need to download it to local storage, and the opposite logic for the opposite scenario
        if re.match(r'^https?://(?:www\.)?youtube\.com/watch\?v=', url):
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f'ytsearch1:"{url}"', download=not stream))

        #Structure for 'data' for a playlist contains 'entries', so this is to check if we want to stream a playlist or a single video
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        #if stream is true, filenam is set to the url, if not, get the filename of the video to download it
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        #cls creates another instance of YTDLSource, and this time, it passes the source - the ffmpeg audio source. it also passes data, which is after * so we must do data = data
        return cls(discord.FFmpegPCMAudio(filename, executable=ffmpeg_path, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn"), data=data)

@bot.command()
async def play(ctx,*, url:str):
    #Checks if the user is in a VC
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
    
    channel = ctx.author.voice.channel
    if ctx.voice_client is None: #If the bot is currently connected to a voice channel
        await channel.connect()

    
    #Add the song to a queue
    await Music_Queue.enqueue(url)
    await ctx.send("Added to queue.")
    await Music_Queue.printqueue(ctx)
    
    #keeps playing the next song in queue
    if not ctx.voice_client.is_playing():
        await playnext(ctx)

async def playnext(ctx):
    if Music_Queue.is_empty():
        await ctx.send("The queue is empty.")
        return
    
    item = Music_Queue.dequeue()
    player = await YTDLSource.from_url(item["url"], loop=bot.loop, stream=True)
    ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(playnext(ctx)))
    
    await ctx.send(f"Now playing: {player.title}")


bot.run(BOT_TOKEN)
