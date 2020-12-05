import youtube_dl
import speech_recognition as speechrec
from os import path
from pydub import AudioSegment
import os
import numpy as np
from tqdm import tqdm
import librosa
import matplotlib.pyplot as plt
from IPython.display import Audio
import threading, queue
import json

key = input("Enter YouTube video key, ie. https://www.youtube.com/watch?v=______ (no entry will default to a presidential debate video): ").strip()
key = "P4L_0C6nA0E" if key == "" else key
url = "https://www.youtube.com/watch?v=%s" % key

config = {'format': 'bestaudio/best',
          'outtmpl': './audio.mp3',
          'postprocessors': [{'key': 'FFmpegExtractAudio',
                              'preferredcodec': 'mp3',
                              'preferredquality': '192'}]}

with youtube_dl.YoutubeDL(config) as ydl:
  ydl.download([url])
  
def clip(filename, target, time, duration):
  os.system("ffmpeg -loglevel warning -ss %s -t %s -i %s %s" % (time, duration, filename, target))
  
def to_wav(filename, target):
  sound = AudioSegment.from_mp3(filename)
  sound.export(target, format = "wav")
  
def alphabetical(char):
  return ord(char) >= 97 and ord(char) <= 122 or ord(char) == 32
  
def move(filepath, target):
  os.rename(filepath, target)
  
def worker(ID):
  global data
  
  r = speechrec.Recognizer()
  r.pause_threshold = 0
  confidence_threshold = 0.5
  duration = 1

  while True:
    time = q.get()
    
    if os.path.exists("clip%s.mp3" % ID): os.remove("clip%s.mp3" % ID)
    if os.path.exists("clip%s.wav" % ID): os.remove("clip%s.wav" % ID)

    clip("audio.mp3", "clip%s.mp3" % ID, time, duration)
    to_wav("clip%s.mp3" % ID, "clip%s.wav" % ID)

    with speechrec.WavFile("clip%s.wav" % ID) as source:
      sound = r.record(source)

    try:
      transcripts = []
      confidences = []

      for alt in r.recognize_google(sound, show_all = True)['alternative']:
        if 'confidence' in alt:
          transcripts.append(alt['transcript'])
          confidences.append(alt['confidence'])

      idx = np.argmax(confidences)
      confidence = confidences[idx]

      if confidence >= confidence_threshold:
        transcript = transcripts[idx].lower()
        transcript = ''.join([char for char in transcript if alphabetical(char)])
        filepath = 'phrases/%s.mp3' % transcript
        
        if transcript in data and confidence > data[transcript]['confidence'] or not transcript in data:
          data[transcript] = {'start': time, 'end': time + duration, 'confidence': confidence}
          move('clip%s.mp3' % ID, 'phrases/%s.mp3' % transcript)
          
          with open('info.json', 'w') as f:
            json.dump(data, f)
    except:
      continue

    q.task_done()
    
data = {}
duration = 1
threads = int(input("Threads: "))
os.mkdir('phrases')

q = queue.Queue()

for ID in range(threads):
  threading.Thread(target = worker, args = (ID,), daemon = True).start()
  
for time in np.arange(0, 1000, duration):
  q.put(time)
  
q.join()
