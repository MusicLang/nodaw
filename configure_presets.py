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
    BBC_SYNTH_PLUGIN = '/Users/floriangardin/code/music/nodaw/data/bbc.vst3'  # extensions: .dll, .vst3, .vst, .component

    # Configure one specific instrument
    import argparse
    import json
    parser = argparse.ArgumentParser(description='Configure presets for a specific instrument')
    parser.add_argument('--instrument', type=str, help='Instrument to configure')
    parser.add_argument('--style', type=str, help='Style of the instrument')
    parser.add_argument('--config', type=str, help='Path to the config directory', default=METADATA_PATH)
    parser.add_argument('--plugin', type=str, help='Path to the plugin', default=BBC_SYNTH_PLUGIN)
    args = parser.parse_args()

    instrument = args.instrument
    style = args.style
    config = args.config
    plugin_path = args.plugin

    presets_path = os.path.join(config, 'presets')

    engine = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)
    bbc_synth = engine.make_plugin_processor("bbc", BBC_SYNTH_PLUGIN)
    # Load metadata
    with open(os.path.join(config, 'metadata.json'), 'r') as f:
        metadata = json.load(f)

    vsts = metadata['vsts']

    plugin = engine.make_plugin_processor("plugin", plugin_path)

    print(instrument, style)
    plugin.open_editor()  # Open the editor, make changes, and close
    state_path = os.path.join(f'{instrument}_{style}.vststate')
    plugin.save_state(os.path.join(config, 'presets', state_path))

    if style == 'all':
        styles = ['legato', 'staccato']
        for style in styles:
            new_tab = {'state': state_path, 'synth_path': plugin_path, 'instrument': instrument, 'style': style}
            # Replace existing in vsts if exists or create new
            for i, tab in enumerate(vsts):
                if tab['instrument'] == instrument and tab['style'] == style:
                    vsts[i] = new_tab
                    break
            else:
                vsts.append(new_tab)
    else:
        new_tab = {'state': state_path, 'synth_path': plugin_path, 'instrument': instrument, 'style': style}

        # Replace existing in vsts if exists or create new
        for i, tab in enumerate(vsts):
            if tab['instrument'] == instrument and tab['style'] == style:
                vsts[i] = new_tab
                break
        else:
            vsts.append(new_tab)

    # Save metadata
    with open(os.path.join(config, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)