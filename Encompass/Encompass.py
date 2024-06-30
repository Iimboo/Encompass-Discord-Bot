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
import matplotlib.pyplot as plt



################################## SET UP ###############################################
BOT_TOKEN = "ENTER BOT TOKEN HERE"
CHANNEL_ID = ENTER CHANNEL ID HERE
WATER_REMINDER_MINUTES = 30
YOUTUBE_API_KEY = "ENTER YOUTUBE API KEY HERE"

bot = commands.Bot(command_prefix ="!", intents=discord.Intents.all())
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
        self.repeat = False
    
    #Adding functions of a queue
    async def enqueue(self,url:str,requester, is_dj = False):
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            self.queue.append({"player" : player, "requester": requester, "is_dj":is_dj, "title": player.title, "url": player.youtube_url})
        except:
            pass
        
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
    'options': '-vn -filter:a "atempo=1.0"' #Tells ffmpeg to skip video stream and process only the audio stream
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options) #YoutubeDL is a class within discord.py, passes in formatting options for the youtube vid

class YTDLSource(discord.PCMVolumeTransformer): #discord.PCMVolumeTransformer is a superclass here, making YTDL the subclass, hence super init allows us to use the init in the superclass
    def __init__(self, source, *, data, youtube_url,volume=0.5): 
        # * means that when calling the function, any variable after * must be specified as keyword arguments: e.g. my_function(c=3) instead of my_function(3)
        
        super().__init__(source, volume) #Calling the init function from the superclass

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.youtube_url = youtube_url

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False): #cls is similar to ctx, just context arguments
        loop = loop or asyncio.get_event_loop() #Gets specified event loop or gets current event loop if event loop is not specified by the user
        
        #run_in_executor used when you want to run a blocking function without blocking the main event loop, uses default executor since "None" is used
        #lambda is used because run_in_executor expects a callable function as it's argument, if you use extract_info directly, you end up passing the returned value instead.
        #when the video is streamable (true), set download to false as there is no need to download it to local storage, and the opposite logic for the opposite scenario
        if re.match(r'^https?://(?:www\.)?youtube\.com/watch\?v=', url):
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        else:
            search_result = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{url}", download=False))
            if search_result and 'entries' in search_result:
                url = search_result['entries'][0]['webpage_url']
                data = search_result['entries'][0]
                
        #Structure for 'data' for a playlist contains 'entries', so this is to check if we want to stream a playlist or a single video
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        #if stream is true, filenam is set to the url, if not, get the filename of the video to download it
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        #Apply equalizer settings
        eq_filters = generate_equalizer_filters(equalizer_settings)
        
        ffmpeg_options = {
            'executable': ffmpeg_path,
            'before_options': "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            'options': f'-vn -filter:a "atempo=1.0" -af "{eq_filters}"'
        }
        #cls creates another instance of YTDLSource, and this time, it passes the source - the ffmpeg audio source. it also passes data, which is after * so we must do data = data
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, youtube_url=url)

def generate_equalizer_filters(settings):
    frequencies = [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    filters = []
    for freq, gain in zip(frequencies, list(settings.values())):
        filters.append(f"equalizer=f={freq}:width_type=o:width=2:g={gain}")
    return ",".join(filters)

#Easy to convert seconds to minutes
def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"

#obtain playlist ID from url
def extract_playlist_id(url):
    query = url.split("?")[1]
    params = query.split("&")
    for param in params:
        if param.startswith("list="):
            return param.split("=")[1]
    return None

##########################################################################################################
#################This section is to handle the music in queue#############################################
async def enqueueremainingsongs_base(ctx,remaining_songs):
    if ctx.voice_client.is_paused() or Music_Queue.repeat:
        return
    
    while len(Music_Queue.queue) < 5 and remaining_songs:
        next_song = remaining_songs.pop(0)
        await Music_Queue.enqueue(next_song['url'],bot.user,is_dj = True)
    
    
    if len(remaining_songs) == 0 and Music_Queue.is_empty():
        await ctx.send("That's it for this jam session! Want to start another one? You know what to do!😉")
        enqueue_remaining_songs.stop()
        
started_tasks =[]
def enqueue_remaining_songs(ctx, remaining_songs):
    task = tasks.loop(seconds=0.01)(enqueueremainingsongs_base)
    started_tasks.append(task)
    task.start(ctx, remaining_songs)               

def stoptask():
    for t in started_tasks:
        t.cancel()
########################################################################################################

#reset the song after equalizing
async def update_playback(ctx):
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        current_source = ctx.voice_client.source
        if hasattr(current_source, 'data'):
            current_url = current_source.youtube_url
            current_title = current_source.title
            current_duration = current_source.data.get('duration', 'Unknown Duration')
            current_thumbnail = current_source.data.get('thumbnail')
            is_dj = current_source.data.get('is_dj', False)
            requester = current_source.data.get('requester', ctx.author)
            player = await YTDLSource.from_url(current_url, loop=bot.loop, stream=True)
            ctx.voice_client.stop()
            ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(playnext(ctx)))
            embed = discord.Embed(title = "**Now Playing**", color = discord.Color.blue())
            embed.add_field(name = "Title", value = current_title, inline = False)
            duration = f"`{format_duration(current_duration)}`"
            embed.add_field(name = "Duration", value = duration, inline = False)
            embed.add_field(name="Recommender", value = bot.user.mention if is_dj else requester.mention, inline = False)
            url = current_url if len(current_url) <= 1024 else current_url[:1021] + "..."
            embed.add_field(name="URL", value = url, inline = False)
            if current_thumbnail:
                embed.set_thumbnail(url = current_thumbnail)
            await ctx.send(embed=embed)

#This function is needed because from_url function is used for individual videos    
async def search_youtube_playlist(genre):
    search_query = f"top {genre} hits playlist"
    request = youtube.search().list(
        q = search_query,
        part = "snippet", #only need the title, duration, etc.
        type = "playlist",
        maxResults = 1
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
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            print(playlist_url)
            item_count = playlist_response['items'][0]['contentDetails']['itemCount']
            if item_count >= 50:
                playlists.append(playlist_id)

    return playlists

async def get_playlist_songs(playlist_id):
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
            songs.append({
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": item['snippet']['title']
            })    
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return songs

@bot.command(help="Shuffles current queue and the remaining playlist songs")
async def shuffle(ctx):
    if not ctx.voice_client.is_playing() or Music_Queue.is_empty():
        await ctx.send("There's nothing to shuffle!")
        return
    if remaining_songs:
        random.shuffle(remaining_songs)
    random.shuffle(Music_Queue.queue)
    await ctx.send("Shuffled!")
    
remaining_songs=[]
@bot.command(help = "Plays a song, queues it instead if there is a song playing. Format: !play <URL/string/playlist URL>", aliases = ['p','P'])
async def play(ctx,*, args:str = commands.parameter(default=None, description=": URL/string/playlist URL and optionally 's' for shuffle")):
            
    if args is None:
        await ctx.send("Enter something...!!!")
        return
    
    args = args.split()
    url = args[0]
    shuffle = args[1] if len(args) > 1 and args[1] in ['s', 'S', 'shuffle'] else None
    if (shuffle != 's' and 'S' and "shuffle" and None):
        await ctx.send("Invalid shuffle option, use '!help play' to find out more.")
        return
    
    #Checks if the user is in a VC
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    
    channel = ctx.author.voice.channel
    if ctx.voice_client is None: #If the bot is currently connected to a voice channel
        await channel.connect()
    
    is_playlist = "playlist" in url

    #Add the song to a queue
    if is_playlist:
        stoptask()
        if ctx.voice_client.is_playing():
            Music_Queue.queue = []
            ctx.voice_client.stop()
            
        if ctx.voice_client is None: #If the bot is currently connected to a voice channel
            await channel.connect()
        playlist_id = extract_playlist_id(url)
        all_songs = await get_playlist_songs(playlist_id)
        print("length of all songs: "+ str(len(all_songs)))
        if not all_songs:
            await ctx.send("No songs found in the playlist.")
            return
        await ctx.send("Loading playlist...")
        if (shuffle == 's' or 'S' or "shuffle"):
            random.shuffle(all_songs)
            await ctx.send("Playlist will be shuffled.")
        if len(all_songs) <= 5:
            for song in all_songs:
                await Music_Queue.enqueue(song['url'],ctx.author,is_dj = False)
            await ctx.send("Loaded playlist!")
            await playnext(ctx)
        else:
            initial_songs = all_songs[:5]
            remaining_songs = all_songs[5:]
            if Music_Queue.is_empty():
                for song in initial_songs:
                    await Music_Queue.enqueue(song['url'], ctx.author, is_dj=False)
                await ctx.send("Loaded playlist!")
                await playnext(ctx)
                
            # Start the task to enqueue remaining songs
            enqueue_remaining_songs(ctx, remaining_songs)
    else:
        if(len(Music_Queue.queue) > 1 or ctx.voice_client.is_playing()):
            await Music_Queue.enqueue(url,ctx.author,is_dj = False)
            await ctx.send("Added to queue.")
        else:
            if Music_Queue.is_empty():
                await Music_Queue.enqueue(url,ctx.author,is_dj = False)
                await playnext(ctx)


@bot.command(help="Toggles repeat mode for the current song")
async def repeat(ctx):
    Music_Queue.repeat = not Music_Queue.repeat
    if Music_Queue.repeat:
        current_player = ctx.voice_client.source
        if current_player:
            current_url = current_player.youtube_url
            current_requester = current_player.data.get('requester')
            current_is_dj = current_player.data.get('is_dj', False)
            await Music_Queue.enqueue(current_url, current_requester, current_is_dj)
            Music_Queue.queue.insert(0, Music_Queue.queue.pop())
        await ctx.send("Repeat mode is now ON🔁")
    else:
        await ctx.send("Repeat mode is now OFF🚫")
        if ctx.voice_client.is_paused() or ctx.voice_client.is_playing():
            #pop out the top song, enqueueremainingsongs will auto run and fill in the gaps
            Music_Queue.dequeue()
        
repeatedurl = ""
async def playnext(ctx):
    if ctx.voice_client.is_paused():
        return
    
    if Music_Queue.is_empty():
        return
    
    item= Music_Queue.dequeue()
    if Music_Queue.repeat:
        await Music_Queue.enqueue(item['url'], item['requester'], item['is_dj'])
        Music_Queue.queue.insert(0, Music_Queue.queue.pop())
    player = item["player"]
    if Music_Queue.repeat:
        repeatedurl = player.youtube_url if len(player.youtube_url) <= 1024 else player.youtube_url[:1021] + "..."

    requester = item["requester"]
    is_dj = item["is_dj"]
    ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(playnext(ctx)))
    
    #Embedding discord messages to make it look more aesthetic
    embed = discord.Embed(title = "**Now Playing**", color = discord.Color.blue())
    embed.title = "Now Playing"
    embed.add_field(name = "Title", value = player.title, inline = False)
    duration = f"`{format_duration(player.data.get('duration','Unknown Duration'))}`"
    embed.add_field(name = "Duration", value = duration, inline = False)
    if requester:
        embed.add_field(name="Recommender", value = bot.user.mention if is_dj else requester.mention, inline = False)
    else:
        embed.add_field(name="Recommender", value = bot.user.mention, inline = False)
    if Music_Queue.repeat:
        url = repeatedurl
    else:
        url = player.youtube_url if len(player.youtube_url) <= 1024 else player.youtube_url[:1021] + "..."
    embed.add_field(name="URL", value = url, inline = False)
    if 'thumbnail' in player.data:
        embed.set_thumbnail(url = player.data['thumbnail'])
    await ctx.send(embed=embed)
    

@bot.command(help = "Skips the current song")
async def skip(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("There's no music playing.")
        return
    if Music_Queue.repeat:
        Music_Queue.repeat = False
        Music_Queue.dequeue()
    
    ctx.voice_client.stop() #playnext(ctx) will automatically be called as it is set as the "after" callback
    await ctx.send("Song skipped.")

@bot.command(help = "Kills the current music session", aliases = ['end'])
async def kill(ctx):
    for t in started_tasks:
        t.cancel()
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel💢")
        return
    
    if ctx.voice_client is None:
        await ctx.send("I'm not connected to a voice channel💢")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("There's no music playing💢")
        return
    
    Music_Queue.clear()
    ctx.voice_client.stop() #playnext(ctx) will automatically be called as it is set as the "after" callback
    await ctx.send("Killed the current session.")

@bot.command(help = "Shows the current queue", aliases = ['q', 'Q'])
async def queue(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    
    if not ctx.voice_client.is_playing() and len(Music_Queue.queue) == 0:
        await ctx.send("There's no music in queue.")
        return
    
    await Music_Queue.printqueue(ctx)

@bot.command(help = "Switches two items in the queue. Format: <reorderq> <item 1> <item 2>")
async def reorderq(ctx,a:int = commands.parameter(default = None,description = ": First queue item to reorder."), b:int = commands.parameter(default = None,description = ": Second queue item to reorder.")):

    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("There's no music in queue.")
        return
    
    if(a > len(Music_Queue.queue) or a <= 0 or b > len(Music_Queue.queue) or b <=0 or a == b or a is None or b is None):
        await ctx.send("Invalid options.")
    
    a -=1
    b -=1
    Music_Queue.queue[a], Music_Queue.queue[b] = Music_Queue.queue[b], Music_Queue.queue[a]
    
    await ctx.send("Queue has been reordered.")
    await Music_Queue.printqueue(ctx)

@bot.command(help = "Pauses the current song")
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

@bot.command(help="Resumes the song", aliases = ['continue'])
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

@bot.command(help="Clears the queue", aliases = ['cq'])
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

@bot.command(help="Starts DJ mode. Format: !dj <whatever genre, artist, etc. you want>", aliases = ['jam', 'DJ'])
async def dj(ctx, *, genre:str = commands.parameter(default = None, description=": Any genre/artist/string can be accepted. A playlist will be chosen from this and will be played.")):
    if genre is None:
        await ctx.send("Choose a genre please.")
        return
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel💢")
        return
    
    if ctx.voice_client is None:
        channel = ctx.author.voice.channel
        await channel.connect()
    
    await ctx.send(f"DJ Mode on! bum-da-bum-tss 🎧\nSetting up... This will only take a moment...")
    
    if ctx.voice_client.is_playing() or len(Music_Queue.queue) != 0:
        await kill(ctx)    
    
    playlists = await search_youtube_playlist(genre)
    if not playlists:
        await ctx.send("Oops... No playlists found, try to tweak your search a little!")
        return
    
    all_songs = []
    initial_songs = []
    remaining_songs = []
    
    selected_playlist = random.choice(playlists)
    all_songs = await get_playlist_songs(selected_playlist)
    random.shuffle(all_songs)
    
    if not all_songs:
        await ctx.send("No songs found in the playlists.")
        return
    
    #Enqueue the first 5 songs
    initial_songs = all_songs[:5]
    for song in initial_songs:
        await Music_Queue.enqueue(song['url'], ctx.author, is_dj=False)

    
    remaining_songs = all_songs[5:]
    await ctx.send("Done setting up! Let's start jamming 🕺💃")
    await playnext(ctx)
    enqueue_remaining_songs(ctx, remaining_songs)
  
######################## EQUALIZER ############################################

#set all frequency to 0 as the default (default mode)
equalizer_settings = {
    '32Hz': 0,
    '64Hz': 0,
    '125Hz': 0,
    '250Hz': 0,
    '500Hz': 0,
    '1kHz': 0,
    '2kHz': 0,
    '4kHz': 0,
    '8kHz': 0,
    '16kHz': 0
}

def generate_equalizer_graph(settings):
    frequencies = list(settings.keys()) #all the frequencies from equalizer_settings
    values = list(settings.values()) #all the values from equalizer_settings

    plt.figure(figsize=(10, 4))
    plt.plot(frequencies, values, marker='o', linestyle='-')
    plt.title('Equalizer')
    plt.xlabel('Frequency')
    plt.ylabel('Gain')
    plt.ylim(-10, 10) #min and max is 10

    plt.savefig('equalizer.png')
    plt.close()

@bot.command(help="Displays the current equalizer settings.", aliases = ['equalizer'])
async def eq(ctx):
    generate_equalizer_graph(equalizer_settings)
    await ctx.send(file=discord.File('equalizer.png'))

@bot.command(help="Sets a value from -10 to 10 for a certain frequency. Format: !eqset <freq> <value>", aliases = ['seteq', 'set'])
async def eqset(ctx, frequency: str = commands.parameter(default = None, description=": Frequency band to adjust (e.g., '32Hz', '64Hz')."), value: int = commands.parameter(default = None, description=": Value to set for the frequency band (-10 to 10).")):
    if frequency is None or value is None:
        await ctx.send("Invalid frequency or value. Please choose the right frequency and make sure your value is within range. Use !eq for more information.")
        return
    if frequency in equalizer_settings and -10 <= value <= 10:
        equalizer_settings[frequency] = value
        await ctx.send(f"Set {frequency} to {value}")
        generate_equalizer_graph(equalizer_settings)
        await ctx.send(file=discord.File('equalizer.png'))
        if ctx.voice_client.is_playing():
            await update_playback(ctx)

    else:
        await ctx.send("Invalid frequency or value. Please ensure the frequency is valid and the value is between -10 and 10.")

@bot.command(help="Increases the value of a certain frequency by one. Format: !equp <freq>")
async def equp(ctx, frequency: str = commands.parameter(default = None, description=": Frequency band to adjust (e.g., '32Hz', '64Hz').")):
    if frequency is None:
        await ctx.send("Please specify a frequency.")
        return
    if frequency in equalizer_settings:
        if equalizer_settings[frequency] < 10:
            equalizer_settings[frequency] += 1
            await ctx.send(f"Increased {frequency} to {equalizer_settings[frequency]}")
            generate_equalizer_graph(equalizer_settings)
            await ctx.send(file = discord.File('equalizer.png'))
            if ctx.voice_client.is_playing():
                await update_playback(ctx)
        else:
            await ctx.send("Invalid frequency or value is already at maximum")
    else:
        await ctx.send("Invalid frequency or value is already at maximum")


@bot.command(help="Decreases the value of a certain frequency by one. Format: !eqdown <freq>")
async def eqdown(ctx, frequency: str = commands.parameter(default = None, description=": Frequency band to adjust (e.g., '32Hz', '64Hz').")):
    if frequency is None:
        await ctx.send("Please specify a frequency.")
        return
    
    if frequency in equalizer_settings:
        if equalizer_settings[frequency] > -10:
            equalizer_settings[frequency] -= 1
            await ctx.send(f"Decreased {frequency} to {equalizer_settings[frequency]}")
            generate_equalizer_graph(equalizer_settings)
            await ctx.send(file = discord.File('equalizer.png'))
            if ctx.voice_client.is_playing():
                await update_playback(ctx)
        else:
            await ctx.send("Invalid frequency or value is already at minimum")
    else:
        await ctx.send("Invalid frequency or value is already at minimum")

@bot.command(help="Resets the equalizer")
async def eqreset(ctx):
    for i in equalizer_settings:
        equalizer_settings[i] = 0
    await ctx.send("Equalizer settings resetted")
    generate_equalizer_graph(equalizer_settings)
    await ctx.send(file = discord.File('equalizer.png'))
    if ctx.voice_client.is_playing():
        await update_playback(ctx)

bot.run(BOT_TOKEN)


