import json
import logging.config
from typing import List

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.api.logging_middleware import LoggingMiddleware, log_config
from core.api.model import ConfigModel, MusicInformationData
from core.service.midi_processing import retrieve_information_from_midi, tokenize_midi_file
from core.service.serializer import TokSequenceEncoder

logging.config.dictConfig(log_config)

app = FastAPI()

origins = ["http://localhost:3000", "https://wimu-frontend-ccb0bbc023d3.herokuapp.com"]

app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

app.add_middleware(LoggingMiddleware, logger=logging.getLogger(__name__))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        content={"success": False, "data": None, "error": "Invalid request parameters"}, status_code=422
    )


@app.post("/process")
async def process(config: ConfigModel = Body(...), file: UploadFile = File(...)) -> JSONResponse:
    try:
        if file.content_type not in ["audio/mid", "audio/midi", "audio/x-mid", "audio/x-midi"]:
            raise HTTPException(status_code=415, detail="Unsupported file type")
        midi_bytes: bytes = await file.read()
        tokens, notes = tokenize_midi_file(config, midi_bytes)
        serialized_tokens = json.dumps(tokens, cls=TokSequenceEncoder)
        serialized_notes = [[note.__dict__ for note in track_notes] for track_notes in notes]
        metrics: MusicInformationData = retrieve_information_from_midi(midi_bytes)
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "tokens": json.loads(serialized_tokens),
                    "notes": serialized_notes,
                    "metrics": json.loads(metrics.model_dump_json())
                },
                "error": None,
            }
        )
    except HTTPException as e:
        return JSONResponse(
            content={"success": False, "data": None, "error": str(e.detail)}, status_code=e.status_code
        )
    except Exception as e:
        return JSONResponse(content={"success": False, "data": None, "error": str(e)}, status_code=500)
