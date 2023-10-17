



FILEPATH = 'data/mastering/references/cinematic.mp3'
FILEPATH = 'data/spotless_mind.m4a'
OUTPUT_PATH = 'data/test.mid'
from musiclang import Score
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

model_output, midi_data, note_events = predict(FILEPATH)

midi_data.write(OUTPUT_PATH)


score = Score.from_midi(OUTPUT_PATH, quantization=4)



score.to_midi('data/test2.mid')
from pdb import set_trace; set_trace()
