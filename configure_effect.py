"""
This file is part of the project "nodaw".
nodaw is a software aiming to provide a simple and efficient way to
control a DAW (Digital Audio Workstation) with a MIDI controller.
nodaw is distributed under the GPL v3 license.

Author: Florian GARDIN

"""

import os
import json
import dawdreamer as daw

if __name__=='__main__':

    METADATA_PATH = 'data/config'
    SAMPLE_RATE = 44100
    BUFFER_SIZE = 128  # Parameters will undergo automation at this buffer/block size.
    PPQN = 960  # Pulses per quarter note.
    DEFAULT_PLUGIN = '/Users/floriangardin/code/music/nodaw/data/reverb.vst3'  # extensions: .dll, .vst3, .vst, .component

    # Configure one specific instrument
    import argparse
    import json
    parser = argparse.ArgumentParser(description='Configure presets for a specific instrument')
    parser.add_argument('--effect', type=str, help='Instrument to configure')
    parser.add_argument('--config', type=str, help='Path to the config directory', default=METADATA_PATH)
    parser.add_argument('--plugin', type=str, help='Path to the plugin', default=DEFAULT_PLUGIN)
    args = parser.parse_args()

    effect = args.effect
    config = args.config
    plugin_path = args.plugin

    presets_path = os.path.join(config, 'presets')

    engine = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)
    synth = engine.make_plugin_processor("bbc", DEFAULT_PLUGIN)
    # Load metadata
    with open(os.path.join(config, 'metadata.json'), 'r') as f:
        metadata = json.load(f)

    effects = metadata['effects']

    plugin = engine.make_plugin_processor("plugin", plugin_path)
    plugin.open_editor()  # Open the editor, make changes, and close
    state_path = os.path.join(f'{effect}.vststate')
    plugin.save_state(os.path.join(config, 'presets', state_path))
    new_tab = {'state': state_path, 'synth_path': plugin_path, 'effect': effect}

    # Replace existing in vsts if exists or create new
    for i, tab in enumerate(effects):
        if tab['effect'] == effect:
            effects[i] = new_tab
            break
    else:
        effects.append(new_tab)

    # Save metadata
    with open(os.path.join(config, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)