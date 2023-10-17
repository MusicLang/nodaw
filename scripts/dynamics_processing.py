




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
METADATA_PATH = os.path.join(BASE_CONFIG_PATH, "metadata.json")
OCTAVES_PATH = 'data/octaves.json'
FORTE_VALUE = 0.3
PIANO_VALUE = 0.05

# Load metadata
with open(CONFIG_PATH, 'r') as f:
    metadata = json.load(f)

with open(OCTAVES_PATH, 'r') as f:
    octaves = json.load(f)


dynamics = ['f', 'p', 'low', 'high']


FORTE = 127
PIANO = 30
HIGH = 1.0
LOW = 0.3


D = {
    'f': (127, 1.0),
    'p': (30, 1.0),
    'low': (127, 0.3),
    'high': (127, 1.0)
}

def has_difference(a, b, tol=0.1):
    return abs((a - b))/abs(a) > tol if abs(a) > 0 else False

instruments = os.listdir(OUTPUT_PATH)
result_dict = {}
for instrument in instruments:
    data_path = os.path.join(OUTPUT_PATH, instrument, "result.json")
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            data = json.load(f)

        touch = has_difference(data['f'], data['p'])
        expression = has_difference(data['low'], data['high'])
        forte_ratio = FORTE_VALUE / data['f'] if data['f'] > 0 else 1.0
        piano_ratio = PIANO_VALUE / data['p'] if data['p'] > 0 else 1.0
        low_ratio = PIANO_VALUE / data['low'] if data['low'] > 0 else 1.0
        high_ratio = FORTE_VALUE / data['high'] if data['high'] > 0 else 1.0

        result_dict[instrument] = {
            "touch": touch,
            "expression": expression,
            "forte_ratio": forte_ratio,
            "piano_ratio": piano_ratio,
            "low_ratio": low_ratio,
            "high_ratio": high_ratio,
            "ratio_up": forte_ratio if touch else high_ratio,
            "ratio_down": piano_ratio if touch else low_ratio,
            "f": data['f'],
            "p": data['p'],
            "low": data['low'],
            "high": data['high']
        }

# Find all entries with "f" key value to 0
zero_values = [key for key, val in result_dict.items() if val['f'] == 0]

print(zero_values)

with open('data/dynamics.json', 'w') as f:
    json.dump(result_dict, f, indent=4)


# Change metadata
with open(METADATA_PATH, 'r') as f:
    metadata = json.load(f)

for whole_instrument, val in result_dict.items():

    is_legato = whole_instrument.endswith('legato')
    instrument = whole_instrument.replace('_legato', '')
    instrument = instrument.replace('_staccato', '')
    style = 'legato' if is_legato else 'staccato'

    # Find metadata
    vsts = [vst for vst in metadata['vsts'] if vst['instrument'] == instrument and vst['style'] == style]
    if len(vsts) > 0:
        vst = vsts[0]

        vst['config'] = val

    else:
        from pdb import set_trace; set_trace()
        print('Not found : ', instrument, style)

# Save
with open(METADATA_PATH, 'w') as f:
    json.dump(metadata, f, indent=4)