#set execution policy to allow the script to run
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

#define the URL for the latest FFmpeg release
$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

#define the paths
$downloadPath = "$env:TEMP\ffmpeg.zip"
$extractPath = "$env:TEMP\ffmpeg"
$finalPath = "C:\ffmpeg"

#download the FFmpeg zip file
Write-Output "Downloading FFmpeg..."
Invoke-WebRequest -Uri $ffmpegUrl -OutFile $downloadPath

#create the extraction directory
Write-Output "Extracting FFmpeg..."
New-Item -ItemType Directory -Force -Path $extractPath

#extract the zip file
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($downloadPath, $extractPath)

#move the extracted files to the final path
Move-Item -Path "$extractPath\*" -Destination $finalPath -Force

#update the system PATH environment variable
$oldPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)
if ($oldPath -notlike "*$finalPath\bin*") {
    $newPath = "$oldPath;$finalPath\bin"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, [System.EnvironmentVariableTarget]::Machine)
    Write-Output "Updated system PATH to include FFmpeg."
} else {
    Write-Output "FFmpeg is already in the system PATH."
}

#clean up
Remove-Item -Path $downloadPath
Remove-Item -Path $extractPath -Recurse

Write-Output "FFmpeg installation and configuration completed."
