# Imagine using camelCase for everything in python.

## What is this?

Python scripts that generate storyboard Sample code based on input midi or Mapping Tools .json (may or may not break if it has other hitsounds than midi imported ones). 

Currently reads all midi tracks as one. hitsound samples are expected to have the note (C1, F#6, etc) in the filename, and all samples should be in the same folder.

Length rounding roughness based on Mapping Tools, so this should Generate similar results.

WIP

## Usage

Commands:
```
-i --input [str] - input file. .mid or  Mapping Tools.json (maybe).
-h --hitsounds [str] - soundbank folder.
-o --offset [int] (default: 0) - When the midi starts "playing" on the map.
-s --shift [int] (default: 0) - Shifts the octave up or down.
-v --volume [int] (default: 100) - What volume to play in the storyboard.
```

```
midi-to-storyboard.py -i [input midi/json] -h [hitsound soundbank (folder)] 
```

Generated files will be in `[folder of the script]/output/[name of the file]` and consists of storyboard.osb and all necessary audio files (that were possible to generate) in the format `[note]-[length].ogg` . Copy audio files to map folder, then open `storyboard.osb` and copy the storyboard script to your `.osu/.osb` of choice (Currently not generating a working `.osb/.osu`, but this might change in the future.)

## Generating Soundbanks
---
So I don't know how to use a VST in python or in general, so this is my workaround for creating set of hitsounds for a range of keys:
1. Generate `notes.mid` by running `piano-midi-gen.py`
2. Open `notes.mid` in your favorite Audio processing software
3. Apply effects and whatever on it.
4. Export as one `.wav`. Make sure to not add any lead-time to the exported file.
5. Run this command:
```
create-sound-bank.py -i [wav file from step 4] -n [soundbank name] -s [first note/midi key] -e [last note/midi key (inclusive)]
```
Examples
```
create-sound-bank.py -i "machinegun.wav" -n machinegun -s "A0" -e "C8"
```

```
create-sound-bank.py -i "harp.wav" -n machinegun -s 21 -e 100
```

