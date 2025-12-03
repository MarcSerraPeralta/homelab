# Managing TV Shows, Anime, and Music libraries in Jellyfin

List of metadata providers for the Jellyfin libraries:
- **TV shows**: imdb
- **Anime**: anidb
- **Music**: musicbrainz

## TV Shows

Follow this steps for TV shows that have more than just one season.

1. All the files need to be transcoded to HEVC 
so that the server does not have to real-time transcoding (computationally expensive).
For that use:
```
transcode_to_hevc.py
```
2. Episodes need to be structured in the correct directories
and they must have the correct imdb tag. For that use:
```
jellyfin_convention_tvshow.py
```
which uses a YAML configuration file for the TV show, such as the one in:
```
jellyfin_convention_tvshow_example.yaml
```
3. Move the files to the server. For that use the command in:
```
copy_to_server.sh
```


## Anime

Follow this steps for Anime that have just one season 
(absolute numbering of the episodes).

1. All the files need to be transcoded to HEVC 
so that the server does not have to real-time transcoding (computationally expensive).
For that use:
```
transcode_to_hevc.py
```
2. Episodes need to be structured in the correct directories
and they must have the correct anidb tag. For that use:
```
jellyfin_convention_anime.py
```
which uses a YAML configuration file for the TV show, such as the one in:
```
jellyfin_convention_anime_example.yaml
```
3. Move the files to the server. For that use the command in:
```
copy_to_server.sh
```


## Music

Follow this steps for music media.

1. Structure the files in the following directory structure:
```
Artist/
    folder.jpg              ---> cover image for the artist
    Album 1/
        folder.jpg          ---> cover image for the album
        music_file.mp3
        ...
    Album 2/
        ...
```
where the `Artist` and `Album` names are taken from the [MusicBrainz database](https://musicbrainz.org/).

2. Open [MusicBrainz Picard](https://picard.musicbrainz.org/) 

    1. Load the artists directories in the GUI
    1. Select all tracks and click `Lookup`
    1. Drag and drop the tracks that were not able to be automatically classified to the correct albums
    1. Click `Save` (to overwrite the files' metadata)

3. Move the files to the server. For that use the command in:
```
copy_to_server.sh
```
