#!/bin/bash

python3 move_classified_pictures_to_hdd.py
python3 delete_all_albums.py
python3 create_album_for_each_external_folder.py
python3 clean_database.py
