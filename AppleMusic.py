import re
import sys
import time
import requests
import urllib.parse
import win32com.client
from pypresence import Presence
from colorama import init, Fore, Style

init()

rpc = None
rpcClient = None
mint = "\033[38;2;52;235;143m"
previousTrack = None

def get_current_track_info():
    try:
        iTunes = win32com.client.Dispatch("iTunes.Application")
        if iTunes.PlayerState == 1:
            return {
                "album": iTunes.CurrentTrack.Album,
                "artist": iTunes.CurrentTrack.Artist,
                "song": iTunes.CurrentTrack.Name,
                "duration": iTunes.CurrentTrack.Duration,
                "position": iTunes.PlayerPosition
            }
        else:
            return None
    except Exception as exception:
        print(f"{Style.BRIGHT}{Fore.RED}Error: {Style.RESET_ALL}{exception}")
        pass

def update_rpc(track_info):
    global previousTrack
    if track_info and track_info != previousTrack:
        print(f"{mint}Currently Playing: {Style.RESET_ALL}{track_info['song']} {mint}by {Style.RESET_ALL}{track_info['artist']}")
        songEncode = urllib.parse.quote(track_info["song"])
        artistEncode = urllib.parse.quote(track_info["artist"])
        albumEncode = urllib.parse.quote(track_info["album"])
        artworkURL = f"https://music.apple.com/us/search?term={artistEncode}%20{albumEncode}"
        response = requests.get(artworkURL)
        url_pattern = re.compile(r'aria-label="{}.*?<source sizes="110px" srcset="(https://[^"]*?)\s110w'.format(re.escape(re.sub(r'[^\w\s]', '', track_info["album"]))), re.DOTALL)
        match = url_pattern.search(response.text)
        if match:
            url = match.group(1)
            url = url.replace("110", "2400").replace("webp", "png")

            rpc.update(
                state=track_info["song"],
                details=track_info["artist"],
                large_image=url,
                large_text=track_info["album"],
                start=int(time.time() - track_info["position"]),
                end=int(time.time() + (track_info["duration"] - track_info["position"])),
            )

def main():
    global rpc, rpcClient, previousTrack
    if "--id" in sys.argv:
        index = sys.argv.index("--id")
        if index + 1 < len(sys.argv):
            rpcClient = sys.argv[index + 1]
            print(f"{mint}RPC Id: {Style.RESET_ALL}{rpcClient}")
    
    if not rpcClient:
        rpcClient = input(f"{mint}RPC Id: {Style.RESET_ALL}")
    
    rpc = Presence(rpcClient)
    rpc.connect()

    try:
        while True:
            track_info = get_current_track_info()
            if track_info and track_info != previousTrack:
                if previousTrack:
                    status = (track_info["song"] != previousTrack["song"] or 
                              track_info["artist"] != previousTrack["artist"] or 
                              track_info["album"] != previousTrack["album"])
                    if status:
                        update_rpc(track_info)
                elif previousTrack is None:
                    update_rpc(track_info)
            elif not track_info:
                rpc.clear()
                previousTrack = None
                time.sleep(1)
            previousTrack = track_info
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    finally:
        rpc.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exception:
        print(f"{Style.BRIGHT}{Fore.RED}Error: {Style.RESET_ALL}{exception}")
