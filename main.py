# VoiceToMidi - Marco Vettore 

import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import mido
from mido import Message



CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

#Max frequency for valid data
NYQUIST_FREQUENCE = int(RATE/2)

p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK
)

#midi out
outport = mido.open_output()

#to remeber the last played note
prevNote = 0

fig = plt.figure(figsize=(5,5))
axes = fig.add_subplot(111)

#X and Y graph limits
axes.set_xlim(0, NYQUIST_FREQUENCE/8)
axes.set_ylim(-1, 10)


point, = axes.plot(np.linspace(0, RATE, CHUNK),np.linspace(0, RATE, CHUNK), 'r')

point.set_linestyle('-')
point.set_linewidth(2)


#Update graph function
def update(frame):
    
    #data read
    data = stream.read(CHUNK)    
    data_np = np.frombuffer(data, dtype='h')

    #Fourier transform
    fft_signal = np.fft.fft(data_np)
    
    xdata = (np.linspace(0, RATE, CHUNK))
    ydata = (np.abs(fft_signal[0:CHUNK])  / (512 * CHUNK))

    point.set_data(xdata, ydata)

    #I pick the the point with max intensity
    maxValueIndex = np.where(ydata == max(ydata))

    #If it's greater the rate/2 i mark as not valid
    if(xdata[maxValueIndex[0][0]] > NYQUIST_FREQUENCE):
        xdata[maxValueIndex[0][0]] = 0
    
    #Filter the good data with intensity with at least 0.5
    if xdata[maxValueIndex[0][0]]>0 and ydata[maxValueIndex[0][0]]>0.5 :

        freq = xdata[maxValueIndex[0][0]]
        velocity = ydata[maxValueIndex[0][0]]

        #Convert the frequency in notes
        note = np.around(12 * np.log2(freq/440.0))

        s=""
        base = note%12

        match base:
            case 0: s= "A"
            case 1: s= "A#"
            case 2: s= "B"
            case 3: s= "C"
            case 4: s= "C#"
            case 5: s= "D"
            case 6: s= "D#"
            case 7: s= "E"
            case 8: s= "F"
            case 9: s= "F#"
            case 10: s= "G"
            case 11: s= "G#"

        #the base note is A4 so i add 4 for the octave
        octave = int(np.floor(note/12) +4)

        noteString = s+ str(octave)
        print(freq, " -> ", note, " -> ", noteString)

        #A4 in midi is 69
        noteMidi = int(note+69)
        
        midiSender(noteMidi)

    else:
        #if the note is not valid or is too low for intensity i only turn off the last note
        midiSender(0)

    return point,



#Function that sends the midi messages
def midiSender(noteMidi):
    global prevNote

    if noteMidi != prevNote:
            
        msg = Message("note_off",note=prevNote)
        outport.send(msg)
        msg = Message("note_on",note=noteMidi)
        outport.send(msg)
        prevNote = noteMidi

    elif noteMidi == 0:
        msg = Message("note_off",note=prevNote)
        outport.send(msg)
        prevNote = 0
         

#Graph animation function
ani = FuncAnimation(fig, update,interval=40 ,blit=True, cache_frame_data=False)

plt.show()