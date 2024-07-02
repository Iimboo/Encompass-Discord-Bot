# Encompass Discord Bot

Encompass is a feature-rich Discord bot designed for music streaming and various other functionalities. This bot utilizes `discord.py`, `yt-dlp`, `google-api-python-client`, `matplotlib`, and `aiohttp` to deliver a robust music streaming experience directly from YouTube.

## Table of Contents

1. [Pre-Setup](#pre-setup)
   - [Important Note](#important-note)
   - [Obtaining Discord Bot Token and Adding the Bot to Your Server](#obtaining-discord-bot-token-and-adding-the-bot-to-your-server)
   - [Getting the YouTube API Key](#getting-the-youtube-api-key)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
   - [Step 1: Install Python](#step-1-install-python)
   - [Step 2: Run the Installation Script](#step-2-run-the-installation-script)
4. [Configuration](#configuration)
5. [Running the Bot](#running-the-bot)
6. [Commands](#commands)
7. [Contributing](#contributing)

## Pre-Setup

### Important Note

The Discord bot token and YouTube API key and Channel ID are essential for the code to run. You must obtain these keys and enter them into the `config.py` file for the bot to function correctly.

### Obtaining Discord Bot Token and Adding the Bot to Your Server

1. Go to the Discord Developer Portal: [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Click on "New Application" and give it a name.
3. Click on "Bot" in the left sidebar, scroll down and check the 3 "Privileged Gateway Intents".
4. On the same "Bot" page, click on "Reset Token", and key in your password if required. This is your BOT TOKEN.
5. Click on "OAuth2" in the left sidebar.
6. Scroll down to the URL generator, check "bot", and give the bot admin privileges in "Bot Permissions" (self-host so it doesn't matter, just give it all permissions).
7. Copy the link below and enter it in your browser, then add your newly created bot to your server.

### Getting the YouTube API Key

1. Go to the Google Cloud Console: [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Log in to your Google account.
3. Click on "Select a project" at the top left, and click on "New Project". Enter a project name and click "Create".
4. In the "Enabled APIs and services" tab (on the left), click on "Enable APIs and services" at the top, search for "YouTube Data API v3" in the search bar, click on it, and click "Enable".
5. At the top right, click "Create Credentials", ensure "YouTube Data API v3" is selected, and choose "Public Data". Click "Next", and your API key should show up. THIS is your YOUTUBE API KEY.

### Obtaining the Channel ID
1. In discord, go to settings, click on "Advanced" at the bottom, and turn on Developer Mode
2. Right click on a server channel you want your music bot to operate in and send messages in, and copy the CHANNEL ID, like so:
![image](https://github.com/Iimboo/Encompass-Discord-Bot/assets/171655348/8a6be135-c4d2-4133-843f-14115d4aabc1)


## Prerequisites

- Windows Operating System
- Administrator privileges

## Installation

### Step 1: Install Python

1. Go to the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download the latest version of Python.
3. Run the Python installer.
4. **Important**: During the installation, make sure to check the box that says "Add Python to PATH". If you skip this step, you will need to add Python to your system environment variables manually.

#### Adding Python to the System Path Manually (If Skipped):

1. Open the Start menu and search for "Environment Variables".
2. Select "Edit the system environment variables".
3. In the System Properties window, click on the "Environment Variables" button.
4. Under "System variables", find the variable named `Path`, and click on it, then click "Edit".
5. In the Edit Environment Variable window, click "New" and add the path to your Python installation (e.g., `C:\Python39` and `C:\Python39\Scripts`).
6. Click "OK" to close all the windows.

### Step 2: Run the Installation Script

1. Open PowerShell as an Administrator:
   - Right-click the Start menu and select "Windows PowerShell (Admin)".
2. Navigate to the directory where you have cloned this repository.
3. Run the installation script by typing the following command and pressing Enter: ".\InstallDependencies.ps1"
4. If prompted with a security warning, type `r` and press Enter to allow the script to run.

### Verify Python Installation

1. Open Command Prompt (you can search for cmd in the Start menu).
2. Type the following command and press Enter:

    python --version

You should see the version of Python you installed. If it does not show the correct version, please refer to Step 1.

## Configuration

1. The file config.py is included in the repository. Open it and fill in the necessary values:

    BOT_TOKEN = "ENTER BOT TOKEN HERE"
    CHANNEL_ID = ENTER CHANNEL ID HERE
    YOUTUBE_API_KEY = "ENTER YOUTUBE API KEY HERE"
    FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe"

- BOT_TOKEN: Your Discord bot token.
- CHANNEL_ID: The ID of the Discord channel where the bot will send messages.
- YOUTUBE_API_KEY: Your YouTube API key.
- FFMPEG_PATH: The path to the ffmpeg.exe file. (Already Provided)

## Running the Bot

1. Open Command Prompt and navigate to the directory where your Encompass.py file is located.
2. Run the bot by typing the following command and pressing Enter:

    python Encompass.py

## Commands

The bot comes with several built-in commands:

- !play <URL or search term>: Plays a song or adds it to the queue.
- !pause: Pauses the current song.
- !resume: Resumes the paused song.
- !skip: Skips the current song.
- !queue: Displays the current queue.
- !clearq: Clears the queue.
- !repeat: Toggles repeat mode for the current song.
- !shuffle: Shuffles the current queue.
- !dj <genre>: Starts DJ mode with a playlist of the specified genre.
- !eq: Displays the current equalizer settings.
- !eqset <frequency> <value>: Sets a value for a specific frequency.
- !equp <frequency>: Increases the value of a specific frequency by one.
- !eqdown <frequency>: Decreases the value of a specific frequency by one.
- !preset <preset_name>: Applies an equalizer preset (e.g., pop, rock, jazz).
- !restart: Restarts the bot.

## Contributing

We welcome contributions! Please open an issue or submit a pull request if you have any improvements or new features to add.

