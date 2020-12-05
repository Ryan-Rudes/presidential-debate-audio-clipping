import youtube_dl
import speech_recognition as speechrec
from os import path
from pydub import AudioSegment
import os, shutil
import numpy as np
from tqdm import tqdm
import librosa
import matplotlib.pyplot as plt
from IPython.display import Audio
import threading, queue
import json

valid = set("abcdefghijklmnopqrstuvwxyz 1234567890")

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
  return char in valid

r = speechrec.Recognizer()
r.pause_threshold = 0
confidence_threshold = 0.9
duration = 1

data = {}
duration = 1
os.mkdir('phrases')

for time in range(1000):
    if os.path.exists("clip.mp3"): os.remove("clip.mp3")
    if os.path.exists("clip.wav"): os.remove("clip.wav")

    clip("audio.mp3", "clip.mp3", time, duration)
    to_wav("clip.mp3", "clip.wav")

    with speechrec.WavFile("clip.wav") as source:
      sound = r.record(source)

    try:
      recognition = r.recognize_google(sound, show_all = True)

      if recognition != []:
        transcripts = []
        confidences = []
        for alt in recognition['alternative']:
          if 'confidence' in alt:
            transcripts.append(alt['transcript'])
            confidences.append(alt['confidence'])

        idx = np.argmax(confidences)
        confidence = confidences[idx]

        if confidence >= confidence_threshold:
          transcript = transcripts[idx].lower().strip()
          new = ""
          bad = False
          for char in transcript:
            if alphabetical(char):
              new += char
            else:
              bad = True
              break

          if not bad:
            transcript = new
            filepath = 'phrases/%s.mp3' % transcript

            if transcript in data and confidence > data[transcript]['confidence'] or not transcript in data:
              data[transcript] = {'start': time, 'end': time + duration, 'confidence': confidence}
              shutil.move('clip.mp3', 'phrases/%s.mp3' % transcript)

              with open('info.json', 'w') as f:
                json.dump(data, f)
    except:
      continue
