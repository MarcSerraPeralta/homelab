# Choice explanation

- Pictures in my phone are always uploaded to Immich in an internal library (`Backup` method in Immich).
- Pictures in an internal library are classified by adding them to albums (via phone or web).
- Every month, the classified pictures in the internal library are moved to my external library,
and deleted from the Immich internal library database (not from phone). See below.
- Pictures in my phone are deleted from my phone if they are more than 1 year old 
and are not in 'Favourites' (`Free Up Space` method in Immich).
- Unclassified pictures in internal library can be obtained by checking the albums
e.g. 'Camera', 'WhatsApp Images' (created by `Backup` method if `Sync Albums` enabled).
This can be used to delete unclassified pictures from the internal libray.

The only thing that is missing in Immich is the moving of the classified pictures
from the interal library to the external library. 
I have created a Python script to do that automatically using the Immich API,
called `move_classified_pictures_to_hdd.py`.
The script perform:
1. Get all albums
1. Check album names
1. Create directories for each new album in the external disk/library
1. Get assets in internal library from albums
1. Move assets from internal library to corresponding external disk/library directory
1. Remove assets from Immich internal library database
1. Rescan external library

I have also created the following scripts, which may be useful:
- `clean_database.py`: deletes any asset in the internal library database that does not 
point to an existing file.
- `create_album_for_each_external_folder.py`: creates new (empty) albums for each folder
in the external disk/library.
- `delete_all_albums.py`: deletes all albums (except marked ones). 
Does not delete the assets associated with them.
- `run_script.sh`: moves all the classified assets to the external library, and
updates all the albums.



# Notes

The internal library of Immich is owned by the docker image.
To check that, run:
```
ls -ld /srv/immich/internal_library
```
The best solution is to add my user to the corresponding group and give the 
group read and write access:
```
sudo usermod -aG systemd-journal marc
newgrp systemd-journal
sudo chmod -R g+rwX /srv/immich/internal_library
sudo chmod g+s /srv/immich/internal_library
```

If the newly created albums do not appear in Immich (via phone), click on the
`Backup` icon in the Home page and wait until everything has updated.
