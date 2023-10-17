
import os
from typing import Optional
from fastapi import UploadFile, File, APIRouter, Depends, Form
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi import FastAPI
from fastapi import Header
from fastapi.middleware.cors import CORSMiddleware
from tempfile import mkstemp
from nodaw.dreamer import DAWPlayer
import json
from fastapi import BackgroundTasks

os.environ["TOKENIZERS_PARALLELISM"] = "false"
origins = [
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:8000",
    "http://localhost:8000/upload",
    "*"
]

app = FastAPI(debug=False)

metadata_path = "data/config"

reference_song_path = "data/mastering/references/cinematic.mp3"
# Post a midi file to the server and returns a wav file

player = DAWPlayer(metadata_path)



def remove_file(path):
    os.remove(path)

@app.post("/render")
async def _render(file: UploadFile = File(...), data: str = Form(...), background_tasks: BackgroundTasks = None):
    import time
    start = time.time()
    options = json.loads(data)
    contents = await file.read()

    # Create temporary file
    fd, path = mkstemp(suffix=".mid")
    # Create temporary output_path
    fd2, output_path = mkstemp(suffix=".wav")

    try:
        with os.fdopen(fd, 'wb') as tmp:
            # Write contents to temporary file
            tmp.write(contents)
        # Process the temporary file
        duration = options['duration']
        player.play(path, output_path, duration=duration)

        print(f"Rendering took {time.time() - start} seconds")

    finally:
        os.remove(path)  # Delete the temporary file

    background_tasks.add_task(remove_file, output_path)

    # Returns a wav file located at output_path
    return FileResponse(output_path, media_type="audio/wav")


@app.post('/master')
async def _master(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    contents = await file.read()

    # Create temporary file
    fd, path = mkstemp(suffix=".wav")
    fd2, output_path = mkstemp(suffix=".wav")
    try:
        with os.fdopen(fd, 'wb') as tmp:
            # Write contents to temporary file
            tmp.write(contents)
        # Process the temporary file
        import matchering as mg
        import time
        start = time.time()
        mg.process(
            # The track you want to master
            target=path,
            # Some "wet" reference track
            reference=reference_song_path,
            # Where and how to save your results
            results=[
                mg.pcm24(output_path),
            ],
        )
        print(f"Mastering took {time.time() - start} seconds")

    finally:
        os.remove(path)

    background_tasks.add_task(remove_file, output_path)

    # Returns a wav file located at output_path
    return FileResponse(output_path, media_type="audio/wav")

