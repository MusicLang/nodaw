


import json

from essentia.standard import MonoLoader, TensorflowPredictMusiCNN, TensorflowPredictVGGish
import numpy as np
import matplotlib.pyplot as plt
import os
FILEPATH = 'data/spotless_mind.m4a'
OUTPUT_PATH = 'data/test.mid'

os.system("wget -q https://essentia.upf.edu/models/autotagging/msd/msd-musicnn-1.pb")
os.system("wget -q https://essentia.upf.edu/models/autotagging/msd/msd-musicnn-1.json")

with open('msd-musicnn-1.json', 'r') as json_file:
    metadata = json.load(json_file)

print(metadata.keys())

audio = MonoLoader(sampleRate=44100, filename=FILEPATH)()

activations = TensorflowPredictMusiCNN(graphFilename='msd-musicnn-1.pb')(audio)

ig, ax = plt.subplots(1, 1, figsize=(10, 10))
ax.matshow(activations.T, aspect='auto')
ax.set_yticks(range(len(metadata['classes'])))
ax.set_yticklabels(metadata['classes'])
ax.set_xlabel('patch number')
ax.xaxis.set_ticks_position('bottom')
plt.title('Tag activations')
plt.show()



