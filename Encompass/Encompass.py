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
        return
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
    async def enqueue(self,url:str,requester, is_dj = False):
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        self.queue.append({"player" : player, "requester": requester, "is_dj":is_dj})

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
            for item in self.queue:
                player = item["player"] 
                await ctx.send(f"{counter}: {player.title}")
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
    'options': '-vn' #Tells ffmpeg to skip video stream and process only the audio stream
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
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f'{url}', download=not stream))

        #Structure for 'data' for a playlist contains 'entries', so this is to check if we want to stream a playlist or a single video
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        #if stream is true, filenam is set to the url, if not, get the filename of the video to download it
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        #cls creates another instance of YTDLSource, and this time, it passes the source - the ffmpeg audio source. it also passes data, which is after * so we must do data = data
        return cls(discord.FFmpegPCMAudio(filename, executable=ffmpeg_path, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn"), data=data)

#Easy to convert seconds to minutes
def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"

@bot.command()
async def play(ctx,*, url:str):
    #Checks if the user is in a VC
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
    
    channel = ctx.author.voice.channel
    if ctx.voice_client is None: #If the bot is currently connected to a voice channel
        await channel.connect()

    #Add the song to a queue
    await Music_Queue.enqueue(url,ctx.author,is_dj = False)
    if(len(Music_Queue.queue) > 1 or ctx.voice_client.is_playing()):
        await ctx.send("Added to queue.")
    
    
    #keeps playing the next song in queue
    if not ctx.voice_client.is_playing():
        await playnext(ctx)

async def playnext(ctx):
    if ctx.voice_client.is_paused():
        return
    
    if Music_Queue.is_empty():
        await ctx.send("The queue is empty.")
        return
    
    item= Music_Queue.dequeue()
    player = item["player"]
    requester = item["requester"]
    is_dj = item["is_dj"]
    ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(playnext(ctx)))
    
    #Embedding discord messages to make it look more aesthetic
    embed = discord.Embed(title = "**Now Playing**", color = discord.Color.blue())
    embed.title = "Now Playing"
    embed.add_field(name = "Title", value = player.title, inline = False)
    duration = f"`{format_duration(player.data.get('duration','Unknown Duration'))}`"
    embed.add_field(name = "Duration", value = duration, inline = False)
    embed.add_field(name="Recommender", value = bot.user.mention if is_dj else requester.mention,inline = False)
    await ctx.send(embed=embed)
    
    
    await ctx.send(f"Now playing: {player.title}")

@bot.command()
async def skip(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("There's no music in queue.")
        return
    
    ctx.voice_client.stop() #playnext(ctx) will automatically be called as it is set as the "after" callback
    await ctx.send("Song skipped")

@bot.command()
async def queue(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("There's no music in queue.")
        return
    
    await Music_Queue.printqueue(ctx)

@bot.command()
async def reorderq(ctx,a:int, b:int):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("There's no music in queue.")
        return
    
    if(a > len(Music_Queue.queue) or a <= 0 or b > len(Music_Queue.queue) or b <=0 or a == b):
        await ctx.send("Invalid options.")
    
    a = a -1
    b = b -1
    temptitle = Music_Queue.queue[a]['title']
    tempurl = Music_Queue.queue[a]['url']
    Music_Queue.queue[a]['title'] = Music_Queue.queue[b]['title']
    Music_Queue.queue[a]['url'] = Music_Queue.queue[b]['url']
    Music_Queue.queue[b]['title'] = temptitle
    Music_Queue.queue[b]['url'] = tempurl
    
    await ctx.send("Queue has been reordered.")
    await Music_Queue.printqueue(ctx)

@bot.command()
async def pause(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel💢")
        return
    
    if ctx.voice_client is None:
        await ctx.send("I'm not connected to a voice channel💢")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("There's no music playing currently💢")
        return
    
    await ctx.send("Paused⌛")
    ctx.voice_client.pause()

@bot.command()
async def resume(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel💢")
        return
    
    if ctx.voice_client is None:
        await ctx.send("I'm not connected to a voice channel💢")
        return
    
    if ctx.voice_client.is_playing():
        await ctx.send("There is music playing already💢")
        return
    
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed⏳")
    else:
        await ctx.send("No music is paused currently💢")

@bot.command()
async def clearq(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel💢")
        return
    
    if ctx.voice_client is None:
        await ctx.send("I'm not connected to a voice channel💢")
        return
    
    if len(Music_Queue.queue) == 0:
        await ctx.send("The queue is empty already💢")
    
    await ctx.send("Queue cleared.")
    Music_Queue.clear()

@bot.command()
async def dj(ctx, *, genre:str):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel💢")
        return
    
    if ctx.voice_client is None:
        channel = ctx.author.voice.channel
        await channel.connect()
    
    await ctx.send(f"DJ Mode on! bum-da-bum-tss 🎧\nSetting up... This will only take a moment...")
    
    
    playlists = await search_youtube_playlist(genre)
    if not playlists:
        await ctx.send("Oops... No playlists found, try to tweak your search a little!")
        return
    
    all_songs = []
    initial_songs = []
    remaining_songs = []
    songs = []
    played_songs = set() #automatic no duplicates, unordered and customizable
    
    selected_playlist = random.choice(playlists)
    all_songs = await get_playlist_songs(selected_playlist, set())
    random.shuffle(all_songs)
    
    if not all_songs:
        await ctx.send("No songs found in the playlists.")
        return
    
    #Enqueue the first 25 songs
    initial_songs = all_songs[:5]
    await asyncio.gather(*[Music_Queue.enqueue(song['url'], bot.user, is_dj=True) for song in initial_songs])

    
    remaining_songs = all_songs[5:]
    await ctx.send("Done setting up! Let's start jamming 🕺💃")
    await playnext(ctx)
    enqueue_remaining_songs.start(ctx, remaining_songs,played_songs, genre)
  
#This function is needed because from_url function is used for individual videos    
async def search_youtube_playlist(genre):
    search_query = f"top {genre} hits playlist"
    request = youtube.search().list(
        q = search_query,
        part = "snippet", #only need the title, duration, etc.
        type = "playlist",
        maxResults = 2
    )
    
    response = await asyncio.to_thread(request.execute) #async required so it doesn't block
    
    playlists = []
    #making a playlistID List
    if response['items']:
        for item in response['items']:
            playlist_id = item['id']['playlistId']
            playlist_request = youtube.playlists().list(
                part = "contentDetails",
                id = playlist_id
            )
            playlist_response = await asyncio.to_thread(playlist_request.execute)
            item_count = playlist_response['items'][0]['contentDetails']['itemCount']
            if item_count >= 50:
                playlists.append(playlist_id)

    return playlists

async def get_playlist_songs(playlist_id, played_songs):
    songs = []
    next_page_token = None
    while True:
        request = youtube.playlistItems().list(
            playlistId=playlist_id,
            part="snippet",
            maxResults=25,  #number of songs to fetch per request
            pageToken=next_page_token
        )
        response = await asyncio.to_thread(request.execute)
        for item in response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            if video_id not in played_songs:
                songs.append({
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": item['snippet']['title']
                })
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return songs

@tasks.loop(seconds = 1)
async def enqueue_remaining_songs(ctx,remaining_songs, played_songs, genre):
    if ctx.voice_client.is_paused():
        return
    while len(Music_Queue.queue) < 5 and remaining_songs:
        next_song = remaining_songs.pop(0)
        await Music_Queue.enqueue(next_song['url'],bot.user,is_dj = True)
    
    if not ctx.voice_client.is_playing() and not Music_Queue.is_empty():
        await playnext(ctx)
    
    if len(remaining_songs) == 0 and len(Music_Queue.queue) == 0:
        await ctx.send("That's it for this jam session! Want to start another one? You know what to do!😉")
        enqueue_remaining_songs.stop()
               
            
bot.run(BOT_TOKEN)
