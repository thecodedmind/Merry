# Merry

A simplistic GUI interface for managing Python modules.

# How it works
The script will query pip, format the response in to a list, and output it in to the GUI.
From here, you can browse the list, select the module you want, and at the press of a button, either update or uninstall.
The script also supports printing out your installed modules and allowing you to uninstall modules like that.
Merry also supports installing modules, pressing Install opens up a little box where you can enter in the module you want to downlod from pip.

# Known issues
The GUI looks like it hangs when its doing the updating/background stuff, everything is still working fine, but it will look frozen.

# Planned features
Adding more pip commands support.

Version Pinning/Locking.

Installing from Git support. (Unsure if this works at all, it might already)

Multi-selecting modules in the listbox.

Fancier GUI.

Virtualenv support. (Currently this works if you run the GUI while sourced in to a virtualenv already)

# Misc info
Tested to work on Python 3.7, probably will not work on earlier versions.
Icon created by https://www.deviantart.com/lustriouscharming

# Requirements
Requires GitPython and Tkinter



