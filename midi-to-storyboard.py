import json
from os import walk, path, makedirs
from shutil import rmtree
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import sys
import getopt


def createMidiKeyMap():
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = 0
    midiKeyMap = {}
    for i in range(21, 128):
        if i % len(notes) == 0:
            octave += 1
        midiKeyMap[i] = notes[i % len(notes)] + str(octave)
    return midiKeyMap


def createKeyToFileMap(midiKeyMap, pathToHitsoundBank):
    filenames = next(walk(pathToHitsoundBank), (None, None, []))[
        2]  # [] if no file
    keyToFileMap = {}
    for key, value in midiKeyMap.items():
        keyToFileMap[key] = next(
            (path.join(pathToHitsoundBank, fileName) for fileName in filenames if value in fileName), "")
    return keyToFileMap


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:vb:vs:v", [
                                   "input=", "bank=", "shift="])
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        sys.exit(2)

    pathToHitsoundBank = None
    pathToMappingToolsJson = None
    pathToOutput = None
    octaveShift = 0

    for o, a in opts:
        if o in ("-i", "--input"):
            pathToMappingToolsJson = a

        elif o in ("-b", "--bank"):
            pathToHitsoundBank = a
        elif o in ("-s, --shift"):
            octaveShift = int(a)
        else:
            assert False, "unhandled option"

    if pathToHitsoundBank is None or pathToMappingToolsJson is None:
        print("missing options")
        sys.exit(2)

    rootDir = path.dirname(path.abspath(__file__))
    outDir = path.join(rootDir, 'output')

    if path.exists(outDir):
        rmtree(outDir)

    makedirs(outDir)
    midiKeyMap = createMidiKeyMap()
    keyToFileMap = createKeyToFileMap(midiKeyMap, pathToHitsoundBank)
    hitsoundGenerator = getHitsoundGenerator(
        midiKeyMap, keyToFileMap, octaveShift, outDir)
    fileName = path.basename(pathToMappingToolsJson)
    with open(pathToMappingToolsJson, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for hitsoundLayer in data["HitsoundLayers"]:
            key = hitsoundLayer["SampleArgs"]["Key"]
            length = hitsoundLayer["SampleArgs"]["Length"]
            keyFile = keyToFileMap[key]
            # If we don't have audio for note, we skip
            if keyFile == "":
                print("Missing file for: key = {}, note = {}".format(
                    key, midiKeyMap[key]))
                continue
            newHitsoundPath = hitsoundGenerator(key, length)
            hitsoundLayer["SampleArgs"]["Path"] = newHitsoundPath
        with open(path.join(outDir, fileName), 'w', encoding='utf-8') as outfile:
            outfile.write(json.dumps(data))


def getHitsoundGenerator(midiKeyMap, keyToFileMap, octaveShift, outDir):
    generatedHitsounds = set()
    fadeOutTime = 300  # ms

    def generateHitsound(key, length):
        key = key+octaveShift*12
        intLength = int(length) + fadeOutTime  # ms
        newHitsoundName = "{}-{}.ogg".format(
            midiKeyMap[key], str(intLength))
        newHitsoundPath = path.join(outDir, newHitsoundName)
        if newHitsoundName in generatedHitsounds:
            return newHitsoundName
        fileExt = keyToFileMap[key].split(".")[-1]
        sourceHitsound = AudioSegment.from_file(
            keyToFileMap[key], format=fileExt)
        newHitsound = sourceHitsound[detect_leading_silence(
            sourceHitsound):intLength]
        newHitsound = newHitsound.fade_out(fadeOutTime)
        newHitsound.export(newHitsoundPath, format="ogg")
        generatedHitsounds.add(newHitsoundName)
        return newHitsoundPath

    return generateHitsound


if __name__ == "__main__":
    main()
