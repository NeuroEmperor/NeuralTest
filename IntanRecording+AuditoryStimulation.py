#Written by Jongha Lee based on Intan TCP communication code March 2024

"""In order to run this script, the IntanRHX should first be started,
and through Network -> Remote TCP Control:

Command Output should open a connection at 127.0.0.1, Port 5000.
Status should read "Pending".

Stimulation code should be implemented in the same file to minimize the latency
"""

#intan recording
import time
import socket
import os
import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import askopenfilename
import numpy as np
import sounddevice as sd
import threading

def play_tone(frequency=2000, duration=2):
    # Play a tone at the given frequency and duration.
    
    fs = 44100  # Sampling rate
    t = np.linspace(0, duration, int(fs * duration), False)  # Time axis
    tone = np.sin(frequency * t * 2 * np.pi)  # Generate sine wave
    sd.play(tone, samplerate=fs)  # Play audio
    sd.wait()  # Wait until the sound has finished playing

def schedule_tone_play(play_times):
    # Schedule the tone to play at the specified times.
    start_time = time.time()
    for play_time in play_times:
        delay = play_time - (time.time() - start_time)
        if delay > 0:
            # Use lambda to specify frequency and duration if needed
            timer = threading.Timer(delay, lambda: play_tone(frequency=2000, duration=1))
            timer.start()

def SaveToDiskDemo():
    """Connects via TCP to RHX software, communicates the file save name and
    location, and records for 5 seconds.
    """

    # Connect to TCP command server - default home IP address at port 5000
    print('Connecting to TCP command server...')
    scommand = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    scommand.connect(('127.0.0.1', 5000))

    # Query runmode from RHX software
    scommand.sendall(b'get runmode')
    commandReturn = str(scommand.recv(COMMAND_BUFFER_SIZE), "utf-8")
    isStopped = commandReturn == "Return: RunMode Stop"

    # If controller is running, stop it
    if not isStopped:
        scommand.sendall(b'set runmode stop')
        # Allow time for RHX software to accept this command before next.
        time.sleep(0.1)

    # Query controller type from RHX software. If Stim, set isStim to true
    scommand.sendall(b'get type')
    commandReturn = str(scommand.recv(COMMAND_BUFFER_SIZE), "utf-8")
    isStim = commandReturn == "Return: Type ControllerStimRecord"

    # Get file save location from user, with the correct file suffix depending
    # on controller type
    print("Please provide a save location and name for incoming data.")
    root = tk.Tk()
    root.withdraw()
    fileSuffix = ".rhs" if isStim else ".rhd"
    fullFileName = filedialog.asksaveasfilename(defaultextension=fileSuffix)
    if not fullFileName:
        print("Canceled")
        return

    # Extract the path and the basefilename (no suffix)
    path = os.path.dirname(fullFileName)
    baseFileName = os.path.basename(fullFileName)[:-4]

    # Send command to RHX software to set baseFileName
    scommand.sendall(b'set filename.basefilename '
                     + baseFileName.encode('utf-8'))
    time.sleep(0.1)

    # Send command to RHX software to set path
    scommand.sendall(b'set filename.path ' + path.encode('utf-8'))
    time.sleep(0.1)

    """
    Insert here the stimulation control
    """
    play_times = [10, 20, 30, 40, 50, 60]  # Example times in seconds from the script start
    start_time = time.time()

    schedule_tone_play(play_times)    
    # Send command to RHX software to begin recording    
    scommand.sendall(b'set runmode record')    
    #######LATENCYEND###########
    end_time = time.time()

    # Wait for 5 seconds
    print("Acquiring data...")
    latency = (end_time - start_time)*1000

    print(f"Latency: {latency} ms")
    time.sleep(5)

    # Send command to RHX software to stop recording
    scommand.sendall(b'set runmode stop')
    time.sleep(0.1)

    # Close TCP socket
    scommand.close()

    # Notify that writing to disk has been completed
    print("Data has been saved to the location: " + fullFileName)


if __name__ == '__main__':
    # Declare buffer size for reading from TCP command socket
    # This is the maximum number of bytes expected for 1 read.
    # 1024 is plenty for a single text command.
    # Increase if many return commands are expected.
    COMMAND_BUFFER_SIZE = 1024

    SaveToDiskDemo()