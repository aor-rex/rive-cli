# rive cli

a simple command-line tool to search movies and tv shows from rivestream links directly in your browser. supports movies, tv episodes, and download links.

---

## installation

```bash
git clone https://github.com/aor-rex/rive-cli.git
cd rive-cli
pip install -r requirements.txt
pip install .
```

## usage

```
rive-cli
rive-cli --download   # for download links
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
