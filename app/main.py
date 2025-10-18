#!/usr/bin/env python3
import requests
import webbrowser
import argparse

TMDB_API_KEY = "11bb49a457474f567dd158ca798b0615"
TMDB_SEARCH_URLS = {
    "movie": "https://api.themoviedb.org/3/search/movie",
    "tv": "https://api.themoviedb.org/3/search/tv"
}
TMDB_TV_DETAILS = "https://api.themoviedb.org/3/tv/{}"
RIVE_EMBED = "https://rivestream.org/embed"
RIVE_DOWNLOAD = "https://rivestream.org/download"

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

def main():
    parser = argparse.ArgumentParser(description="RiveStream CLI — open embed or download link in browser")
    parser.add_argument("--download", action="store_true", help="Open the download link instead of the embed")
    args = parser.parse_args()

    query = input("🎬 Enter show or movie name: ").strip()
    results = search_tmdb(query)

    if not results:
        print("❌ No matches found on TMDB.")
        return

    # List search results
    print("\n🔍 Search results:")
    for i, item in enumerate(results, 1):
        print(f"{i}. {item['title']} ({item['year']}) [{item['type']}]")

    choice = input("\n📝 Select the number of the correct title: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(results)):
        print("❌ Invalid selection.")
        return
    selected = results[int(choice) - 1]
    print(f"\n✅ Selected: {selected['title'].upper()} ({selected['year']})")

    season = episode = None
    if selected["type"] == "tv":
        seasons = get_tv_seasons(selected["id"])
        print("\n📺 Available seasons:")
        for s in seasons:
            print(f"{s['season_number']}. {s['name']} ({s.get('episode_count', '?')} episodes)")

        season_choice = input("\n📝 Select season number: ").strip()
        if not season_choice.isdigit() or int(season_choice) not in [s['season_number'] for s in seasons]:
            print("❌ Invalid season.")
            return
        season = int(season_choice)

        episodes = get_tv_episodes(selected["id"], season)
        print(f"\n🎞️ Episodes in Season {season}:")
        for ep in episodes:
            print(f"{ep['episode_number']}. {ep['name']}")

        episode_choice = input("\n📝 Select episode number: ").strip()
        if not episode_choice.isdigit() or int(episode_choice) not in [ep['episode_number'] for ep in episodes]:
            print("❌ Invalid episode.")
            return
        episode = int(episode_choice)

    url = build_rive_url(selected["type"], selected["id"], season, episode, download=args.download)
    action = "Download" if args.download else "Watch"
    print(f"\n🌍 Opening {action} URL in browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    main()
