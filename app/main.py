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

CACHE_PATH = Path.home() / ".rive-cli" / "cache.json"
CACHE_PATH.parent.mkdir(exist_ok=True)
CACHE_EXPIRY = 24 * 3600 

def search_tmdb(query):
    results = []
    for media_type, url in TMDB_SEARCH_URLS.items():
        r = requests.get(url, params={"api_key": TMDB_API_KEY, "query": query})
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
    r = requests.get(TMDB_TV_DETAILS.format(tv_id), params={"api_key": TMDB_API_KEY})
    data = r.json()
    seasons = data.get("seasons", [])
    return [s for s in seasons if s.get("season_number", 0) > 0]

def get_tv_episodes(tv_id, season_number):
    r = requests.get(TMDB_TV_DETAILS.format(tv_id) + f"/season/{season_number}", params={"api_key": TMDB_API_KEY})
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
    parser = argparse.ArgumentParser(description="RiveStream CLI — open embed or download link in browser")
    parser.add_argument("-m", "--movie", help="Quick command: open a movie by name or TMDB ID")
    parser.add_argument("-t", "--tv", help="Quick command: open a TV show by name or TMDB ID")
    parser.add_argument("-s", "--season", help="Season number for TV show")
    parser.add_argument("-e", "--episode", help="Episode number for TV show")
    parser.add_argument("-d", "--download", action="store_true", help="Open the download link instead of the embed")
    args = parser.parse_args()

    # Determine query
    if args.movie:
        query = args.movie
    elif args.tv:
        query = args.tv
    else:
        query = input("🎬 Enter show or movie name: ").strip()

    results = search_tmdb_cached(query)
    if not results:
        print("❌ No matches found")
        return

    # Use fzf selection if multiple results
    if len(results) == 1:
        selected = results[0]
    else:
        options = [f"{item['title']} ({item['year']}) [{item['type']}]" for item in results]
        selected_index = select_with_fzf(options)
        if selected_index is None:
            print("❌ No selection made.")
            return
        selected = results[selected_index]

    print(f"\n✅ Selected: {selected['title'].upper()} ({selected['year']})")

    season = episode = None
    if selected["type"] == "tv":
        seasons = get_tv_seasons(selected["id"])
        if args.season:
            season = int(args.season)
        else:
            season_options = [f"{s['season_number']}. {s['name']} ({s.get('episode_count','?')} eps)" for s in seasons]
            season_index = select_with_fzf(season_options)
            if season_index is None:
                print("❌ No season selected.")
                return
            season = seasons[season_index]['season_number']

        episodes = get_tv_episodes(selected["id"], season)
        if args.episode:
            episode = int(args.episode)
        else:
            episode_options = [f"{ep['episode_number']}. {ep['name']}" for ep in episodes]
            episode_index = select_with_fzf(episode_options)
            if episode_index is None:
                print("❌ No episode selected.")
                return
            episode = episodes[episode_index]['episode_number']

    url = build_rive_url(selected["type"], selected["id"], season, episode, download=args.download)
    icon = "⬇️" if args.download else "▶️"
    print(f"\n{icon} Now Playing: {selected['title'].upper()} ({selected['year']})")
    webbrowser.open(url)



if __name__ == "__main__":
    main()
