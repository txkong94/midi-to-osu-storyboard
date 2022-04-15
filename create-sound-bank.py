from pydub import AudioSegment, effects
from pydub.silence import split_on_silence
import os
import sys
import getopt
import json
import math
import pprint
from shutil import rmtree


def createMidiKeyToNoteMap():
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = 0
    midiKeyToNoteMap = {}
    for i in range(21, 128):
        if i % len(notes) == 0:
            octave += 1
        midiKeyToNoteMap[i] = notes[i % len(notes)] + str(octave)
    return midiKeyToNoteMap


def createNoteToMidiKeyMap():
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = 0
    noteToMidiKeyMap = {}
    for i in range(21, 128):
        if i % len(notes) == 0:
            octave += 1
        noteName = notes[i % len(notes)] + str(octave)
        noteToMidiKeyMap[noteName] = i
    return noteToMidiKeyMap


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:n:p:", [
            "input=", "name=", "padding="])
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        sys.exit(2)

    pathToInput = None
    nameOfSoundBank = None
    padding = 0  # ms
    for o, a in opts:
        if o in ("-i", "--input"):
            pathToInput = a
        elif o in ("-n", "--name"):
            nameOfSoundBank = a
        elif o in ("-p", "--padding"):
            padding = int(a)
        else:
            assert False, "unhandled option"

    if pathToInput is None:
        print("No input detected")
        sys.exit(2)

    midiKeyToNoteMap = createMidiKeyToNoteMap()
    noteToMidiKeyMap = createNoteToMidiKeyMap()
    rootDir = os.path.dirname(os.path.abspath(__file__))
    outDir = os.path.join(rootDir, 'soundbanks', nameOfSoundBank)
    fileExt = pathToInput.split(".")[-1]

    sourceSounds = AudioSegment.from_file(
        pathToInput, format=fileExt)

    if os.path.exists(outDir):
        rmtree(outDir)
    os.makedirs(outDir)

    twoSecondsInMs = 2000
    fiveSecondsInMs = 5000
    currentTime = 0
    hitsoundBankDict = {}
    for key in range(21, 128):
        dictValue = ''
        startTime = currentTime
        endTime = currentTime+twoSecondsInMs + padding
        newNote = sourceSounds[startTime:endTime]
        if not math.isinf(newNote.dBFS):
            dictValue = os.path.join(
                outDir, "{}.ogg".format(midiKeyToNoteMap[key]))
            try:
                out = effects.normalize(newNote).export(
                    dictValue, format="ogg")
            finally:
                out.close()
        hitsoundBankDict[key] = dictValue
        currentTime += twoSecondsInMs + fiveSecondsInMs
    pprint.pprint(hitsoundBankDict)
    with open(os.path.join(outDir, 'hitsoundbank.json'), 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(hitsoundBankDict))


if __name__ == "__main__":
    main()
