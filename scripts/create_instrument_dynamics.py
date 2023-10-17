import json
import time

import dawdreamer as daw
import os
import shutil
from scipy.io import wavfile
import numpy as np
from nodaw.dreamer import float2pcm

SAMPLE_RATE = 44100
BUFFER_SIZE = 512  # Parameters will undergo automation at this buffer/block size.

OUTPUT_PATH = 'data/dynamics'
BASE_CONFIG_PATH = 'data/config'
CONFIG_PATH = 'data/config/metadata.json'

OCTAVES_PATH = 'data/octaves.json'

# Load metadata
with open(CONFIG_PATH, 'r') as f:
    metadata = json.load(f)

with open(OCTAVES_PATH, 'r') as f:
    octaves = json.load(f)


dynamics = ['f', 'p', 'low', 'high']

D = {
    'f': (127, 1.0),
    'p': (30, 1.0),
    'low': (127, 0.3),
    'high': (127, 1.0)
}

def render(pitch, filepath, synth, engine, maxtime=0.3, expression=None, velocity=127):
    # Configure synth
    if expression is not None:
        params = synth.get_parameters_description()
        param_expression = [i for i, param in enumerate(params) if param['name'].lower() in ['expression', 'volume']]
        synth.set_parameter(param_expression[0], expression)

    # Add midi note
    synth.add_midi_note(pitch, velocity, 0.0, maxtime)

    graph = [
        (synth, []),
        # (reverb, [synth.get_name()])  # effect needs 2 channels, and "synth" provides those 2.
    ]
    engine.load_graph(graph)
    engine.render(maxtime)
    synth.clear_midi()
    audio = engine.get_audio().transpose()[:, [0, 1]]
    mixed_audio = float2pcm(audio)
    wavfile.write(filepath, SAMPLE_RATE, mixed_audio)
    average_energy = np.sqrt(np.mean(audio **2))
    return float(average_energy)


def play_note(vst):

    # Load synth
    engine = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)
    instrument = vst['instrument']
    dynamic = vst['style']
    synth_path = os.path.abspath(vst['synth_path'])
    state_path = os.path.join(BASE_CONFIG_PATH, 'presets', vst['state'])
    synth = engine.make_plugin_processor(vst['instrument'] + "_" + vst['style'], synth_path)
    res = synth.load_state(os.path.abspath(state_path))
    params = synth.get_plugin_parameters_description()

    # Play notes in each dynamic, expression, octaves
    octave_played = octaves.get(instrument, [3, 5])
    octave_played = int((octave_played[0] + octave_played[1]) / 2)
    note_played = (octave_played + 2) * 12
    instrument_path = os.path.abspath(os.path.join(OUTPUT_PATH, instrument + "_" + dynamic))

    if not os.path.exists(instrument_path):
        os.mkdir(instrument_path)
    # Play the note

    result_dict = {}

    for volume in dynamics:
        filename = f"{volume}.wav"
        filepath = os.path.join(instrument_path, filename)
        velocity, expression = D[volume]
        average_energy = render(note_played, filepath, synth, engine, expression=expression, velocity=velocity)
        result_dict[volume] = average_energy

    # Save result_dict
    with open(os.path.join(instrument_path, "result.json"), 'w') as f:
        json.dump(result_dict, f)


vsts = metadata['vsts']

# Filter only acoustic bass
#vsts = [vst for vst in vsts if vst['instrument'] == 'acoustic_bass']

for instrument in vsts:
    try:
        play_note(instrument)
    except Exception as e:
        print(f"Error for {instrument}")
        print(e)
        continue
