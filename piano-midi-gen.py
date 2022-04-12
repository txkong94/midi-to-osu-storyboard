# I dunno how you would generate sounds from a VST,
# so instead here's a midi that plays every note on
# a piano that you can give to your DAW of choice,
# and export a wav that you can then create a sound
# bank with create-sound-bank.py

from mido import MidiFile, MidiTrack, Message, second2tick

outfile = MidiFile()
track = MidiTrack()
defaultTempo = 500000
ticksPerBeat = outfile.ticks_per_beat
outfile.tracks.append(track)
timeToPlay = int(second2tick(
    2, ticksPerBeat, defaultTempo))
timeToWait = int(second2tick(
    5, ticksPerBeat, defaultTempo))
for i in range(21, 128):
    track.append(Message('note_on', note=i, velocity=100,
                 time=(0 if i == 21 else timeToWait)))
    track.append(Message('note_off', note=i, velocity=0, time=timeToPlay))


outfile.save('notes.mid')
