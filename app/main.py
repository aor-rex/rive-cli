#!/usr/bin/env python3
import requests
import webbrowser
import argparse
import json
import os
from pathlib import Path
import subprocess
import time


TMDB_API_KEY = "11bb49a457474f567dd158ca798b0615"
TMDB_SEARCH_URLS = {
    "movie": "https://api.themoviedb.org/3/search/movie",
    "tv": "https://api.themoviedb.org/3/search/tv"
}
TMDB_TV_DETAILS = "https://api.themoviedb.org/3/tv/{}"
RIVE_EMBED = "https://rivestream.org/embed"
RIVE_DOWNLOAD = "https://rivestream.org/download"
VIDSRC_EMBED = "https://vidsrc-embed.ru/embed"
VIDSRC_VIP = "https://dl.vidsrc.vip"


CACHE_PATH = Path.home() / ".rive-cli" / "cache.json"
CACHE_PATH.parent.mkdir(exist_ok=True)
CACHE_EXPIRY = 24 * 3600 

def safe_get(url, params=None, retries=3):
    for i in range(retries):
        try:
            return requests.get(url, params=params, timeout=30)
        except requests.exceptions.Timeout:
            print(f"⚠️ request timed out, retrying {i+1}/{retries}...")
        except requests.exceptions.ConnectionError:
            print("❌ no internet connection.")
            exit(1)
    print("❌ failed after multiple retries.")
    exit(1)


def build_vidsrc_url(media_type, tmdb_id, season=None, episode=None, download=False):
    if download:
        if media_type == "tv":
            return f"{VIDSRC_VIP}/tv/{tmdb_id}/{season}/{episode}"
        elif media_type == "movie":
            return f"{VIDSRC_VIP}/movie/{tmdb_id}"
    else:
        if media_type == "movie":
            return f"{VIDSRC_EMBED}/movie?tmdb={tmdb_id}"
        elif media_type == "tv":
            return f"{VIDSRC_EMBED}/tv?tmdb={tmdb_id}&season={season}&episode={episode}"
    return None

def search_tmdb(query):
    results = []
    for media_type, url in TMDB_SEARCH_URLS.items():
        r = safe_get(url, params={"api_key": TMDB_API_KEY, "query": query})
        for item in r.json().get("results", []):
            results.append({
                "title": item.get("title") or item.get("name"),
                "year": (item.get("release_date") or item.get("first_air_date") or "")[:4],
                "id": item["id"],
                "type": media_type
            })
    return results


def search_tmdb_cached(query):
    cache = load_cache()
    now = time.time()

    if query in cache:
        cached_time = cache[query]["time"]
        if now - cached_time < CACHE_EXPIRY:
            print("🗂 using cached results")
            return cache[query]["results"]
        
    results = search_tmdb(query)  
    cache[query] = {
        "time": now,
        "results": results
    }
    save_cache(cache)
    return results
def get_tv_seasons(tv_id):
    r = safe_get(TMDB_TV_DETAILS.format(tv_id), params={"api_key": TMDB_API_KEY})
    data = r.json()
    seasons = data.get("seasons", [])
    return [s for s in seasons if s.get("season_number", 0) > 0]

def get_tv_episodes(tv_id, season_number):
    r = safe_get(TMDB_TV_DETAILS.format(tv_id) + f"/season/{season_number}", params={"api_key": TMDB_API_KEY})
    data = r.json()
    return data.get("episodes", [])

def build_rive_url(media_type, tmdb_id, season=None, episode=None, download=False):
    base = RIVE_DOWNLOAD if download else RIVE_EMBED
    if media_type == "tv":
        return f"{base}?type=tv&id={tmdb_id}&season={season}&episode={episode}"
    return f"{base}?type=movie&id={tmdb_id}"

def load_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)

def select_with_fzf(options):
    fzf = subprocess.Popen(
        ["fzf", "--ansi", "--prompt=🔍 Select: "],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    stdout, _ = fzf.communicate(input="\n".join(options))
    if not stdout:
        return None
    return options.index(stdout.strip())

def main():
    parser = argparse.ArgumentParser(description="rive-cli — open embed or download link in browser")
    parser.add_argument("-m", "--movie", help="open a movie by name")
    parser.add_argument("-t", "--tv", help="open a tv show by name")
    parser.add_argument("-s", "--season", help="season number for tv show")
    parser.add_argument("-e", "--episode", help="episode number for tv show")
    parser.add_argument("-d", "--download", action="store_true", help="go to download")
    parser.add_argument("-p", "--provider", choices=["rive", "vidsrc"], default="rive", help="choose provider (rive, vidsrc)")

    args = parser.parse_args()

    
    if args.movie:
        query = args.movie
    elif args.tv:
        query = args.tv
    else:
        query = input("🎬 enter show or movie name: ").strip()

    results = search_tmdb_cached(query)
    if not results:
        print("❌ no matches found")
        return

    if len(results) == 1:
        selected = results[0]
    else:
        options = [f"{item['title']} ({item['year']}) [{item['type']}]" for item in results]
        selected_index = select_with_fzf(options)
        if selected_index is None:
            print("❌ no selection made.")
            return
        selected = results[selected_index]

    print(f"\n✅ selected: {selected['title'].upper()} ({selected['year']})")

    season = episode = None
    if selected["type"] == "tv":
        seasons = get_tv_seasons(selected["id"])
        if args.season:
            season = int(args.season)
        else:
            season_options = [f"{s['season_number']}. {s['name']} ({s.get('episode_count','?')} eps)" for s in seasons]
            season_index = select_with_fzf(season_options)
            if season_index is None:
                print("❌ no season selected.")
                return
            season = seasons[season_index]['season_number']

        episodes = get_tv_episodes(selected["id"], season)
        if args.episode:
            episode = int(args.episode)
        else:
            episode_options = [f"{ep['episode_number']}. {ep['name']}" for ep in episodes]
            episode_index = select_with_fzf(episode_options)
            if episode_index is None:
                print("❌ no episode selected.")
                return
            episode = episodes[episode_index]['episode_number']

    if args.provider == "vidsrc":
        url = build_vidsrc_url(selected["type"], selected["id"], season, episode, download=args.download)
    else:
        url = build_rive_url(selected["type"], selected["id"], season, episode, download=args.download)

    icon = "⬇️" if args.download else "▶️"

    if args.download:
        if selected["type"] == "tv":
            print(f"\n{icon} start downloading: {selected['title'].upper()} — S{season:02d}E{episode:02d}")
        else:
            print(f"\n{icon} start downloading: {selected['title'].upper()} ({selected['year']})")
    else:
        if selected["type"] == "tv":
            print(f"\n{icon} start watching: {selected['title'].upper()} — S{season:02d}E{episode:02d}")
        else:
            print(f"\n{icon} start watching: {selected['title'].upper()} ({selected['year']})")


    webbrowser.open(url)



if __name__ == "__main__":
    main()