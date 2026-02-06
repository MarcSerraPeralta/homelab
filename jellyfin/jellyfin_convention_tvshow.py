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

if set(conf) < set(["name", "year", "path"]):
    raise ValueError("YAML file must contain 'name', 'year', and 'path'.")

name, year, path = conf["name"], conf["year"], conf["path"]
if not isinstance(name, str):
    raise TypeError(f"'name' must be a string, not {type(name)}.")
if not isinstance(year, int):
    raise TypeError(f"'year' must be an int, not {type(year)}.")
if not isinstance(path, str):
    raise TypeError(f"'path' must be a string, not {type(path)}.")
path = pathlib.Path(path)

imdb = conf.get("imdb")
jellyfin_tvshows_path = pathlib.Path(conf.get("jellyfin_tvshows_path", "Shows"))
jellyfin_tvshows_path.mkdir(exist_ok=True, parents=True)

tvshow_name = f"{name} ({year})"
if imdb is not None:
    tvshow_name += f" [imdbid-{imdb}]"
jellyfin_tvshow_path = jellyfin_tvshows_path / tvshow_name
jellyfin_tvshow_path.mkdir(exist_ok=True, parents=True)

seasons = []
for key in conf:
    if not isinstance(key, str):
        continue
    if key[:7] != "season_":
        continue
    if not key[7:].isnumeric():
        raise ValueError(f"Seasons must be formatted as 'season_X', not {key}.")
    seasons.append(int(key[7:]))

# ensure one leading 0 in names
mls = max([len(str(s)) for s in seasons])

for season in seasons:
    season_name = f"season_{season}"

    if set(conf[season_name]) != set(["subdirectory", "name_format"]):
        raise ValueError(f"{season_name} must contain 'subdirectory' and 'name_format'.")

    subdirectory, name_format = conf[season_name]["subdirectory"], conf[season_name]["name_format"]
    if not isinstance(subdirectory, str):
        raise ValueError(f"{season_name} 'subdirectory' must be a string, not {type(subdirectory)}.")
    if not isinstance(name_format, str):
        raise ValueError(f"{name_format} 'name_format' must be a string, not {type(name_format)}.")

    season_path = path / subdirectory
    if not season_path.exists():
        raise ValueError(f"{season_path} does not exist.")

    new_season_name = f"Season 0{season:0{mls}d}"
    jellyfin_season_path = jellyfin_tvshow_path / new_season_name
    jellyfin_season_path.mkdir(exist_ok=True, parents=True)

    episode_names = sorted(os.listdir(season_path))
    episodes = []
    for episode_name in episode_names:
        match = re.search(name_format, episode_name)
        if match:
            episode = int(match.group(1))
        else:
            raise ValueError(f"No match for {episode_name} in {season_name} when using '{name_format}'.")

        episodes.append(episode)

    # ensure one leading 0 in names
    mle = max([len(str(e)) for e in episodes])

    for episode, episode_name in zip(episodes, episode_names):
        _, extension = os.path.splitext(episode_name)
        new_episode_name = f"{name} S0{season:0{mls}d}E0{episode:0{mle}d}{extension}"

        if DRY_RUN:
            if ABSOLUTE_PATH:
                print(season_path / episode_name, "->", jellyfin_season_path / new_episode_name)
            else:
                print(pathlib.Path(subdirectory) / episode_name, "->", pathlib.Path(tvshow_name) / new_season_name / new_episode_name)
        else:
            shutil.move(season_path / episode_name, jellyfin_season_path / new_episode_name)
