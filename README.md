# rive cli

a simple command-line tool to search movies and tv shows from [rivestream](https://www.rivestream.org/) directly in your browser. supports movies, tv episodes, and download links.

---
## dependecies 
- fzf

## installation

```bash
git clone https://github.com/aor-rex/rive-cli.git
cd rive-cli
pip install -r requirements.txt
pip install .
```

## options

```
    -h, --help            show this help message and exit
    -m, --movie MOVIE     open a movie by name
    -d, --download        go to download
    -t, --tv TV           open a tv show by name
    -s, --season SEASON   season number for tv show
    -e, --episode EPISODE episode number for tv show
```
## usage

```
rive-cli                 # interactive mode
rive-cli -d  "the beekeper"   # open download link
rive-cli -m "conjuring"   # quick movie
rive-cli -t "johnny test" -s 2 -e 3  # quick tv episode

```