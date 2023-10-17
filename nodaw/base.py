import json
import os


class NoDaw:


    def __init__(self, config_directory: str):
        """
        Create a NoDaw instance which is the main object that allows you to play a midi file with real vsts instruments.

        :param config_directory:
        """
        self.config_directory = config_directory

        self.metadata = json.load(open(os.path.join(self.config_directory, 'metadata.json'), 'r'))