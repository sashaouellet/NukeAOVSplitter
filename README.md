# NukeAOVSplitter
A simple tool for shuffling out AOVs.

## Setup
1. Go to the "Clone or Download" green button at the top right of this repository and click "Download ZIP"
2. Unzip the contents anywhere you'd like, you should now have a folder called ``NukeAOVSplitter-master``
3. Locate your ``.nuke`` folder in your computer's home directory:
* For Windows: ``C:\Users\YOUR_USERNAME\.nuke``
* For Linux: ``/home/YOUR_USERNAME/.nuke``
4. Copy the CONTENTS of the ``NukeAOVSplitter-master`` folder (not the folder itself) into the ``.nuke`` folder you just found
5. Restart Nuke

*Optionally* (recommended), you can append the location of the ``NukeAOVSplitter-master`` folder to the environment variable ``NUKE_PATH`` and Nuke should load everything on startup.

## Usage
1. Select any Read node that has AOV channel data.
2. A dialog will appear showing you the AOVs that have been found. You can uncheck those that you don't want shuffled out.
3. Select any secondary options to add Grade nodes, Denoise, and/or re-merge the results.
