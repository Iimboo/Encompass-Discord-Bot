#set execution policy to allow the script to run
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Check if FFmpeg is already installed
if (-Not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    # Define the URL for the latest FFmpeg release
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    # Define the paths
    $downloadPath = "$env:TEMP\ffmpeg.zip"
    $extractPath = "$env:TEMP\ffmpeg"
    $finalPath = "C:\ffmpeg"

    # Download the FFmpeg zip file
    Write-Output "Downloading FFmpeg..."
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $downloadPath

    # Create the extraction directory
    Write-Output "Extracting FFmpeg..."
    New-Item -ItemType Directory -Force -Path $extractPath

    # Extract the zip file
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($downloadPath, $extractPath)

    # Move the extracted files to the final path
    Move-Item -Path "$extractPath\*" -Destination $finalPath -Force

    # Update the system PATH environment variable
    $oldPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)
    if ($oldPath -notlike "*$finalPath\bin*") {
        $newPath = "$oldPath;$finalPath\bin"
        [System.Environment]::SetEnvironmentVariable("Path", $newPath, [System.EnvironmentVariableTarget]::Machine)
        Write-Output "Updated system PATH to include FFmpeg."
    } else {
        Write-Output "FFmpeg is already in the system PATH."
    }

    # Clean up
    Remove-Item -Path $downloadPath
    Remove-Item -Path $extractPath -Recurse

    Write-Output "FFmpeg installation and configuration completed."
} else {
    Write-Output "FFmpeg is already installed."
}

# Function to install Python packages using pip
function Install-PythonPackage {
    param (
        [string]$packageName
    )
    try {
        Write-Output "Installing $packageName..."
        & python -m pip install $packageName
        Write-Output "$packageName installation completed."
    } catch {
        Write-Error "Failed to install $packageName. Error: $_"
    }
}


# Install the required Python packages
$packages = @(
    "discord.py",
    "yt-dlp",
    "google-api-python-client",
    "matplotlib",
    "aiohttp",
    "PyNaCl"
)

foreach ($package in $packages) {
    Install-PythonPackage -packageName $package
}

Write-Output "All dependencies have been installed."