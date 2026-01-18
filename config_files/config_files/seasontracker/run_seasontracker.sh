#!/bin/bash

source /home/marc/config_files/seasontracker/venv/bin/activate
seasontracker notify /home/marc/config_files/seasontracker/my_tracked_seasons.yaml
deactivate
