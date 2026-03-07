# Wii emulation

```
Emulator software: Dolphin
Controllers: original Wiimotes
Bluetooth hardware for original Wiimotes: Mayflash Dolphin bar
Operating system: Windows 11
Downloading games: vimm.net
```

Note that: 
- one can also use other types of controllers like keyboard or Xbox controllers, see section about config files.
- the dolphin bar seems to also work in some Linux distros (see issue [#53](https://github.com/MarcSerraPeralta/homelab/issues/53))
- there is an open issue in Moonlight to use the wii motes from a remote PC (see issue [#53](https://github.com/MarcSerraPeralta/homelab/issues/53))
- other types of controllers (checked for Xbox controller and keyboard) can be used from a remote PC (see issue [#53](https://github.com/MarcSerraPeralta/homelab/issues/53))


## Config files

The `.ini` files inside `config_files/` map the controls from e.g. keyboard or Xbox controller to the Wiimote actions. 
These config files are game specific as the best mapping choice depends on the controls of the game.
To load the config file in Dolphin:
```
Controllers > Wii Remotes > Emulate the Wii's Bluetooth adapter > select "Emulated Wii Remote" for Wii Remote X > Configure
```
then
```
Profile (top right) > Select the .ini file > Load
```

Dolphin looks for these files inside the following directory (for Windows):
```
C:\Users\<YourUserName>\AppData\Roaming\Dolphin Emulator\Config\Profiles\Wiimote
```

The files inside `config_files/` have the following nomenclature:
```
{controller}-{wii game}.ini
```
