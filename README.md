# Import Alphafold2 model into PyMOL using a plugin
PyMOL plugin to import Alphafold2 models hosted by EMBL, based on fetch-functionality

The Alphafold Protein Structure Database hosted at EMBL is awesome, but it would be even better if you could load the structures directly from PyMOL, like you can for a PDB structure. Now you can, just install the attached plugin and load in your protein based on UniProtID.

## Installation instructions:
* Download the files as .zip by clicking the green 'Code' button, and 'Download ZIP'.
* Open PyMOL, and in the menu bar click Plugin -> Plugin Manager
* Click the tab 'Install new plugin' and then the button 'Choose file', select the .zip
* Accept the default plugin installation directory or change to your preference

You should now have the entry 'Import Alphafold2 entry from EMBL' in your plugin menu.

If the module fails to initialize, you might have to install the `requests` module. From within the embedded PyMOL command line, run:
```
import subprocess 
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install","requests"])
```
And retry initializing the plugin (easiest by restarting PyMOL). 

If you have PyMOL installed via conda, you can also run `conda install requests` in the conda environment.

## Loading multiple entries:
Want to use the command line or load multiple objects at once? Just type in:

    fetchAF2 uniprot1 uniprot2 ... uniprotN, name1 name2 ... nameN
    
(names are optional, the syntax is identical to 'fetch' used to import PDB)
