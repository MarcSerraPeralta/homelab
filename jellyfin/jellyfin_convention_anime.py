import os
import pathlib
import shutil
import argparse
import yaml
import re

parser = argparse.ArgumentParser(description="Organizes and names files according to Jellyfin's convention")
parser.add_argument(
    "yaml_conf",
    type=pathlib.Path,
    help="YAML configuration file for the TV show"
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Does not actually move the files, just prints what is going to happen"
)
parser.add_argument(
    "--absolute-path",
    action="store_true",
    help="In dry run, prints absolute path (not relative)"
)
args = parser.parse_args()
DRY_RUN = args.dry_run
ABSOLUTE_PATH = args.absolute_path

with open(args.yaml_conf, "r") as stream:
    conf = yaml.safe_load(stream)

if set(conf) < set(["name", "year", "path", "name_format"]):
    raise ValueError("YAML file must contain 'name', 'year', and 'path'.")

name, year, path, name_format = conf["name"], conf["year"], conf["path"], conf["name_format"]
if not isinstance(name, str):
    raise TypeError(f"'name' must be a string, not {type(name)}.")
if not isinstance(year, int):
    raise TypeError(f"'year' must be an int, not {type(year)}.")
if not isinstance(path, str):
    raise TypeError(f"'path' must be a string, not {type(path)}.")
if not isinstance(name_format, str):
    raise TypeError(f"'name_format' must be a string, not {type(name_format)}.")
path = pathlib.Path(path)

anidb = conf.get("anidb")
jellyfin_animes_path = pathlib.Path(conf.get("jellyfin_animes_path", "Animes"))
jellyfin_animes_path.mkdir(exist_ok=True, parents=True)

anime_name = f"{name} ({year})"
if anidb is not None:
    anime_name += f" [anidbid-{anidb}]"
jellyfin_anime_path = jellyfin_animes_path / anime_name
jellyfin_anime_path.mkdir(exist_ok=True, parents=True)

new_season_name = "Season 01"
jellyfin_season_path = jellyfin_anime_path / new_season_name
jellyfin_season_path.mkdir(exist_ok=True, parents=True)

episodes, episode_names = [], []
for subpath, subdirs, files in os.walk(path):
    for episode_name in files:
        match = re.search(name_format, episode_name)
        if match:
            episode = int(match.group(1))
        else:
            raise ValueError(f"No match for {episode_name} in {subpath} when using '{name_format}'.")

        rel_subpath = os.path.relpath(subpath, path)

        episodes.append(episode)
        episode_names.append((rel_subpath, episode_name))

# ensure one leading 0 in names
mle = max([len(str(e)) for e in episodes])

for episode, (subpath, episode_name) in zip(episodes, episode_names):
    _, extension = os.path.splitext(episode_name)
    new_episode_name = f"{name} S01E0{episode:0{mle}d}{extension}"

    if DRY_RUN:
        if ABSOLUTE_PATH:
            print(path / subpath / episode_name, "->", jellyfin_season_path / new_episode_name)
        else:
            print(pathlib.Path(subpath) / episode_name, "->", pathlib.Path(anime_name) / new_season_name / new_episode_name)
    else:
        shutil.move(path / subpath / episode_name, jellyfin_season_path / new_episode_name)
