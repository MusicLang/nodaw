import mido
import sched
import time
from .constants import DEFAULT_CONFIG, REVERSE_INSTRUMENT_DICT
import json
import numpy as np
import mido
from mido import MidiFile

import dawdreamer as daw
from scipy.io import wavfile
import subprocess
import os
import tempfile
import pickle
SAMPLE_RATE = 44100
BUFFER_SIZE = 512  # Parameters will undergo automation at this buffer/block size.
FORTE = 127
PIANO = 30
HIGH = 1.0
LOW = 0.3

def float2pcm(sig, dtype='int16'):
    sig = np.asarray(sig)
    dtype = np.dtype(dtype)
    i = np.iinfo(dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig * abs_max + offset).clip(i.min, i.max).astype(dtype)

def get_default_config():
    pass
class DAWPlayer:



    def __init__(self, metadata_path, config=DEFAULT_CONFIG):
        self.metadata_path = metadata_path
        self.metadata = self.load_metadata(metadata_path)
        self.vsts = self.metadata['vsts']
        self.vsts_dict = {
            (value['instrument'], value['style']): value for value in self.vsts
        }
        self.effects = self.metadata['effects']
        self.default_instrument_key = (self.metadata['default_vst']['instrument'], self.metadata['default_vst']['style'])
        self.synths = {}
        self.engine = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)
        self.duration = 10
    def load_metadata(self, metadata_path):
        with open(os.path.join(metadata_path, 'metadata.json'), 'r') as f:
            metadata = json.load(f)
        return metadata

    @property
    def reverb_effect(self):
        reverb_effect = [effect for effect in self.effects if effect['effect'] == 'reverb'][0]
        return reverb_effect

    def load_synths(self, instruments):
        # Load only synths that are not loaded yet
        #self.synths = {}
        default_synth = self.metadata['default_vst']
        for metadata in self.vsts:
            name = f"{metadata['instrument']}_{metadata['style']}"
            synth_path = metadata['synth_path']
            state_path = os.path.join(self.metadata_path, 'presets', metadata['state'])
            instrument = metadata['instrument']
            style = metadata['style']
            is_default_synth = instrument == default_synth['instrument'] and style == default_synth['style']
            if (instrument, style) not in instruments and not is_default_synth:
                continue
            if (instrument, style) in self.synths.keys():
                continue
            print('loading synth :', metadata['instrument'], metadata['style'])
            engine = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)
            synth = engine.make_plugin_processor(name, synth_path)
            synth.load_state(state_path)
            self.synths[(instrument, style)] = (synth, engine, metadata['config'])

        # Load also the default synth
        time.sleep(5)
        return self.synths

    def duration_to_dynamic(self, instrument, duration):
        if duration > 0.4:
            channel = 'legato'
        else:
            channel = 'staccato'

        return channel

    def get_all_instrument_automation(self, notes):
        for (instrument, dynamic), (synth, engine, config) in self.synths.items():

            if config['expression'] and not config['touch']:
                self.get_instrument_automation(synth, notes, instrument, dynamic)

    def get_instrument_automation(self, synth, notes, instrument, dynamic):

        # instrument, time, pitch, dynamic, duration, velocity
        # Filter notes of the instrument
        filtered_notes = [note for note in notes if note[0] == instrument and note[3] == dynamic]
        # Sort by time
        filtered_notes = list(sorted(filtered_notes, key=lambda x: x[1]))

        time_velocities = [(note[1], note[5]) for note in filtered_notes]
        time_vector = np.linspace(0, self.duration, int(SAMPLE_RATE * self.duration))
        amp_vector = np.zeros_like(time_vector)

        for idx, (time, velocity) in enumerate(time_velocities):
            next_velocity = time_velocities[idx+1][1]/127 if idx < len(time_velocities) - 1 else 0
            next_velocity = (next_velocity + 1) * 0.5
            next_time = int(time_velocities[idx+1][0] * SAMPLE_RATE) if idx < len(time_velocities) - 1 else int(self.duration * SAMPLE_RATE)
            new_time = int(time * SAMPLE_RATE)
            new_velocity = velocity / 127
            new_velocity = (1 + new_velocity) * 0.5
            amp_vector[new_time:next_time] = np.linspace(new_velocity, next_velocity, next_time - new_time)

        # Group by time at sample rate
        params = synth.get_parameters_description()
        param_expression = [i for i, param in enumerate(params) if param['name'].lower() in ['expression', 'volume']]
        param_expression = param_expression[0]
        amp_vector = np.linspace(0, 1.0, int(SAMPLE_RATE * self.duration))
        synth.set_automation(param_expression, amp_vector)

    def add_midi_note(self, instrument, time, pitch, dynamic, duration, velocity):
        synth, engine, config = self.synths.get((instrument, dynamic), self.synths[self.default_instrument_key])
        if duration > 0:
            if config['expression']:
                real_velocity = FORTE
            else:
                real_velocity = velocity
            synth.add_midi_note(pitch, real_velocity, time, duration)  # (MIDI note, velocity, start, duration)
        # With `beats=True`, we can use beats as the unit for the start time and duration.
        # Rest for a beat and then play a note for a half beat.
        #synth.add_midi_note(67, 127, 1, .5, beats=True)


    def correct_audio(self, audio, config):

        min, max = [PIANO, FORTE] if config['touch'] else [LOW, HIGH]



    def render(self, filepath, maxtime):
        time.sleep(1)
        reverb_effect = self.reverb_effect
        reverb_path = reverb_effect['synth_path']
        #engine = list(self.synths.items())[0][1][1]
        #reverb = engine.make_plugin_processor("effect", reverb_path)
        #reverb.load_state(os.path.join(self.metadata_path, 'presets', reverb_effect['state']))
        audios = []
        for key, (synth, engine, config) in self.synths.items():

            graph = [
                (synth, []),
                #(reverb, [synth.get_name()])  # effect needs 2 channels, and "synth" provides those 2.
            ]
            engine.load_graph(graph)
            engine.render(maxtime)
            synth.clear_midi()
            audio = engine.get_audio().transpose()[:, [0, 1]]

            # FIXME : Maybe change velocities instead of raw audios
            audio *= ((config['ratio_up']))

            audios.append(audio)

        mixed_audio = audios.pop()
        for audio in audios:
            mixed_audio = mixed_audio + audio
        import math
        mixed_audio = mixed_audio / math.sqrt(len(self.synths))
        print('MAX', np.max(mixed_audio))
        mixed_audio = mixed_audio / np.max(mixed_audio)
        # Convert float32 mixed_audio to int16.
        #mixed_audio = float2pcm(mixed_audio)
        wavfile.write(filepath, SAMPLE_RATE, mixed_audio)

        # for idx, synth in enumerate(self.synths.values()):
        #     graph = [
        #         (synth, [])
        #     ]
        #     engine.load_graph(graph)
        #     engine.render(maxtime)
        #
        #     audio = engine.get_audio()  # shaped (2, N samples)
        #     wavfile.write(filepath.replace('.wav', f'{idx}.wav'), SAMPLE_RATE, audio.transpose())

    @staticmethod
    def midi_file_to_array(midi_path):
        mid = MidiFile(midi_path)

        ongoing_notes = {i: {} for i in range(len(mid.tracks))}  # ongoing notes for each track
        current_program = [0] * len(mid.tracks)  # current program for each track
        current_time = [0] * len(mid.tracks)  # current time for each track
        current_tempo = mido.bpm2tempo(120)
        output = []
        print('TICKS PER BEATS', mid.ticks_per_beat)
        for i, track in enumerate(mid.tracks):
            msgs_in_track = [msg
                              for msg in track]
            for msg in msgs_in_track:
                # Convert time from ticks to seconds

                current_time[i] += mido.tick2second(msg.time, mid.ticks_per_beat, current_tempo)
                if msg.type == 'note_on' and msg.velocity > 0:
                    note_info = {'pitch': msg.note, 'velocity': msg.velocity, 'duration': 0,
                                 'offset': current_time[i],
                                 'channel': msg.channel,
                                 'instrument': current_program[i]
                                 }
                    ongoing_notes[i][msg.note] = note_info

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in ongoing_notes[i]:
                        note_info = ongoing_notes[i].pop(msg.note)
                        note_info['duration'] = current_time[i] - note_info['offset']  # set duration
                        output.append(note_info)
                elif msg.type == 'program_change':
                    current_program[i] = REVERSE_INSTRUMENT_DICT[msg.program]
                elif msg.type == 'set_tempo':
                    current_tempo = msg.tempo

        return output


    def play(self, midi_file, output_path, duration=8):
        import time

        start = time.time()
        #self.play_midi_multiproc(midi_file, output_path, duration)
        self.play_midi(midi_file, output_path, duration)
        print('time taken', time.time() - start)

    def parse_events_separate_tracks(self, events, metadata):

        metadata_by_tracks = {
            (m['instrument'], m['style']): m for m in metadata

        }

        notes_by_track = {}
        for event in events:
            pitch = event['pitch']
            velocity = int(event['velocity'])
            note_duration = float(event['duration'])
            offset = float(event['offset'])
            instrument = event['instrument']
            if note_duration <= 0:
                continue
            dynamic = self.duration_to_dynamic(instrument, note_duration)
            track = (instrument, dynamic)
            notes_by_track.setdefault(track, []).append({
                'pitch': pitch,
                'velocity': velocity,
                'duration': note_duration,
                'offset': offset,
            })

        tracks = [
            {
                'notes': value,
                'instrument': key[0],
                'dynamic': key[1],
                "vst": metadata_by_tracks.get(key, self.metadata['default_vst'])['synth_path'],
                "state": metadata_by_tracks.get(key, self.metadata['default_vst'])['state'],
                'name': f'{key[0]}_{key[1]}'
            }
            for key, value in notes_by_track.items()
        ]


        return tracks

    def play_midi_multiproc(self, midi_file, output_path, duration=8):
        events = self.midi_file_to_array(midi_file)
        tracks = self.parse_events_separate_tracks(events, self.vsts)
        render_duration = float(duration + 2)
        # Create a config file in a tempfile
        with tempfile.NamedTemporaryFile('w', delete=True) as f:
            config_path = f.name
            output_dir = tempfile.mkdtemp()
            config = {
                  "output_dir": output_dir,
                  "render_duration": render_duration,
                  "tracks": tracks
            }
            # get the tracks
            with open(config_path, 'w') as f:
                json.dump(config, f)

            import os, glob, shutil
            subprocess.call(['python', 'app/test_player.py',
                             '--config-path', config_path,
                             '--output-kind', 'pkl',
                             ])
            pkl_files = glob.glob(os.path.join(output_dir, '*.pkl'))
            # Mix the sounds together and output to output_path
            mixed_audio = None
            for file in pkl_files:
                # Read the pickle file
                with open(file, 'rb') as f:
                    data = pickle.load(f)
                if mixed_audio is None:
                    mixed_audio = data
                else:
                    mixed_audio += data

            mixed_audio = float2pcm(mixed_audio)

            # Write the audio to a wav file
            wavfile.write(output_path, SAMPLE_RATE, mixed_audio)
            # Remove output_dir
            shutil.rmtree(output_dir)


    def parse_events(self, events, duration=8):
        notes = []
        instruments = set()
        max_time = 0
        for event in events:
            pitch = event['pitch']
            velocity = int(event['velocity'])
            note_duration = float(event['duration'])
            offset = float(event['offset'])
            instrument = event['instrument']
            if note_duration <= 0:
                continue
            dynamic = self.duration_to_dynamic(instrument, note_duration)
            max_time = max(max_time, offset)
            notes.append((instrument, offset, pitch, dynamic, note_duration, velocity))
            instruments.add((instrument, dynamic))

        max_time = duration + 2

        return notes, instruments, max_time

    def play_midi(self, midi_file, output_path, duration=8):
        """
                Stream a score to the appropriate MIDI ports
                Events are of the form :
                {
                      'duration': 1.5,
                      'pitch': 0,
                      'offset': 0.0,
                      'velocity': 114.0,
                      'instrument': 'piano',
                      'silence': 0,
                      'pedal': None
                    }
                """
        self.duration = duration
        events = self.midi_file_to_array(midi_file)
        notes, instruments, max_time = self.parse_events(events, duration)
        self.load_synths(instruments)
        self.get_all_instrument_automation(notes)
        for note in notes:
            self.add_midi_note(*note)
        self.render(output_path, max_time)