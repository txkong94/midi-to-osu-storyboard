import json
from os import walk, path, makedirs
from shutil import rmtree
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import sys
import getopt
import pprint
import mido
import math


def createMidiKeyMap():
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = 0
    midiKeyMap = {}
    for i in range(21, 128):
        if i % len(notes) == 0:
            octave += 1
        midiKeyMap[i] = notes[i % len(notes)] + str(octave)
    return midiKeyMap


def createOrGetKeyToFileMap(midiKeyMap, pathToHitsoundBank):
    keyToFileMap = {}
    hitsoundBankPath = path.join(
        pathToHitsoundBank, 'hitsoundbank.json')
    if(path.isfile(hitsoundBankPath)):
        with open(hitsoundBankPath, 'r', encoding='utf-8') as f:
            keyToFileMap = json.load(
                f, object_hook=lambda x: {int(k): v for k, v in x.items()})
            # pprint.pprint(keyToFileMap)
            return keyToFileMap

    filenames = next(walk(pathToHitsoundBank), (None, None, []))[
        2]  # [] if no file
    for key, value in midiKeyMap.items():
        keyToFileMap[key] = next(
            (path.join(pathToHitsoundBank, fileName) for fileName in filenames if value in fileName), "")
    with open(path.join(hitsoundBankPath), 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(keyToFileMap))
    return keyToFileMap


def getHitsoundGenerator(midiKeyMap, keyToFileMap, octaveShift, outDir):
    generatedHitsounds = set()
    fadeOutTime = 300  # ms

    def generateHitsound(key, length):
        key = key+octaveShift*12

        keyFile = keyToFileMap[key]
        # If we don't have audio for note, we skip
        if keyFile == "":
            print("Missing file for: key = {}, note = {}".format(
                key, midiKeyMap[key]))
            return ("", "")

        intLength = int(length) + fadeOutTime  # ms
        newHitsoundName = "{}-{}.ogg".format(
            midiKeyMap[key], str(intLength))
        newHitsoundPath = path.join(outDir, newHitsoundName)
        if newHitsoundName in generatedHitsounds:
            return newHitsoundName
        fileExt = keyFile.split(".")[-1]
        sourceHitsound = AudioSegment.from_file(
            keyFile, format=fileExt)
        newHitsound = sourceHitsound[detect_leading_silence(
            sourceHitsound):intLength]
        newHitsound = newHitsound.fade_out(fadeOutTime)
        newHitsound.export(newHitsoundPath, format="ogg")
        generatedHitsounds.add(newHitsoundName)
        return (newHitsoundName, newHitsoundPath)

    return generateHitsound


def readMappingToolsJson(pathToJson):
    samples = {}
    with open(pathToJson, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for hitsoundLayer in data["HitsoundLayers"]:
            key = int(hitsoundLayer["SampleArgs"]["Key"])
            length = int(hitsoundLayer["SampleArgs"]["Length"])
            times = hitsoundLayer["Times"]
            samples[(key, length)] = [int(time) for time in times]
    # print(sorted(samples, key=lambda key: (key[0], key[1])))
    # print(len(samples.keys()))
    return samples

# Same implementation as Mapping Tools
# https://github.com/OliBomby/Mapping_Tools/blob/master/Mapping_Tools/Classes/HitsoundStuff/HitsoundImporter.cs
# RoundLength


def roundLength(length, roughness=1):
    roughPow = math.pow(length, 1 / roughness)
    roughRound = math.ceil(roughPow)
    return round(math.pow(roughRound, roughness))


def readMidi(pathToMidi):
    mid = mido.MidiFile(pathToMidi)
    ticksPerBeat = mid.ticks_per_beat
    samples: dict = {}
    for i, track in enumerate(mid.tracks):
        trackTempo = 0
        cumulativeTime = 0
        noteOnDict = {}
        for msg in track:
            cumulativeTime += msg.time
            if msg.is_meta:
                if msg.type == 'set_tempo':
                    trackTempo = msg.dict()['tempo']
            elif msg.type == 'note_on' and msg.velocity != 0:
                noteOnDict[msg.note] = cumulativeTime
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                noteStart = noteOnDict.pop(msg.note)
                noteLength = cumulativeTime - noteStart
                if noteLength != 0:
                    msNoteLength = mido.tick2second(
                        noteLength, ticksPerBeat, trackTempo) * 1000
                    key = (msg.note, roundLength(msNoteLength))
                    samples.setdefault(key, []).append(noteStart)
    # print(sorted(samples, key=lambda key: (key[0], key[1])))
    # print(len(samples.keys()))
    return samples


def writeStoryboard(outDir, samples, hitsoundGenerator, offset=0, volume=40):
    if path.exists(outDir):
        rmtree(outDir)
    makedirs(outDir)

    with open(path.join(outDir, "storyboard.osb"), 'w', encoding='utf-8') as outfile:
        lines = []
        for sample in samples.items():
            key, length = sample[0]
            times = sample[1]
            hitsoundName, hitsoundPath = hitsoundGenerator(key, length)
            for time in times:
                lines.append((time + offset, hitsoundName))
        lines.sort(key=lambda line: line[0])
        for line in lines:
            outfile.write("Sample,{},0,\"{}\",{}\n".format(
                line[0], line[1], volume))


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:vh:vb:vs:vo:v", [
            "input=", "hitsounds=", "shift=", "offset=", "beatmap="])
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        sys.exit(2)

    pathToHitsoundBank = None
    pathToMappingToolsJson = None
    pathToMidi = None
    pathToOutput = None
    pathToBeatmap = None
    octaveShift = 0
    offset = 0
    for o, a in opts:
        if o in ("-i", "--input"):
            ext = path.splitext(a)[1].lower()
            if ext == '.mid':
                pathToMidi = a
            elif ext == '.json':
                pathToMappingToolsJson = a
            else:
                assert False, "Unsupported input"
        elif o in ("-h", "--hitsounds"):
            pathToHitsoundBank = a
        elif o in ("-b", "--beatmap"):
            pathToBeatmap = a
        elif o in ("-s", "--shift"):
            octaveShift = int(a)
        elif o in ("-o", "--offset"):
            offset = int(a)
        else:
            assert False, "unhandled option"

    if pathToHitsoundBank is None or (pathToMappingToolsJson is None and pathToMidi is None):
        print("missing options")
        sys.exit(2)

    rootDir = path.dirname(path.abspath(__file__))
    outDir = path.join(rootDir, 'output')

    midiKeyMap = createMidiKeyMap()
    keyToFileMap = createOrGetKeyToFileMap(midiKeyMap, pathToHitsoundBank)
    hitsoundGenerator = getHitsoundGenerator(
        midiKeyMap, keyToFileMap, octaveShift, outDir)

    samples = {}
    if pathToMappingToolsJson is not None:
        samples = readMappingToolsJson(pathToMappingToolsJson)
    elif pathToMidi is not None:
        samples = readMidi(pathToMidi)

    if not samples:
        print("No samples generated")
        sys.exit(0)

    writeStoryboard(outDir,
                    samples, hitsoundGenerator, offset)


if __name__ == "__main__":
    main()
