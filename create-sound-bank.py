from pydub import AudioSegment, effects
from pydub.silence import split_on_silence
import os
import sys
import getopt
import json
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
        opts, args = getopt.getopt(sys.argv[1:], "i:vn:vs:ve:v", [
            "input=", "name=", "start=", "end="])
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        sys.exit(2)

    pathToInput = None
    nameOfSoundBank = None
    start = 21
    end = 88
    for o, a in opts:
        if o in ("-i", "--input"):
            pathToInput = a
        elif o in ("-n", "--name"):
            nameOfSoundBank = a
        elif o in ("-s", "--start"):
            start = a
        elif o in ("-e", "--end"):
            end = a
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

    startKey = noteToMidiKeyMap[start] if start in noteToMidiKeyMap else int(
        start)
    endKey = noteToMidiKeyMap[end] if end in noteToMidiKeyMap else int(
        end)

    sourceSounds = AudioSegment.from_file(
        pathToInput, format=fileExt)

    # noteChunks = split_on_silence(
    #     sourceSounds, min_silence_len=3000, silence_thresh=-60)

    if os.path.exists(outDir):
        rmtree(outDir)
    os.makedirs(outDir)

    index = 0
    twoSecondsInMs = 2000
    fiveSecondsInMs = 5000
    currentTime = 0
    hitsoundBankDict = {}
    for key in range(21, 128):
        dictValue = ''
        if key in range(startKey, endKey+1):
            dictValue = os.path.join(
                outDir, "{}.ogg".format(midiKeyToNoteMap[key]))
            startTime = currentTime
            endTime = currentTime+twoSecondsInMs
            try:
                newNote = sourceSounds[startTime:endTime]
                out = effects.normalize(newNote).export(
                    dictValue, format="ogg")
            finally:
                out.close()
        hitsoundBankDict[key] = dictValue
        index += 1
        currentTime += twoSecondsInMs + fiveSecondsInMs

    with open(os.path.join(outDir, 'hitsoundbank.json'), 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(hitsoundBankDict))


if __name__ == "__main__":
    main()
