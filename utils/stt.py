import base64
import json
import os
import aiohttp
from utils.logger import logger

async def transcribe_audio(file_bytes, file_format="wav"):
    """
    Transcribes audio using OpenRouter's Whisper Large V3 Turbo.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found in environment variables.")
        return None

    base64_audio = base64.b64encode(file_bytes).decode("utf-8")
    
    url = "https://openrouter.ai/api/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "openai/whisper-large-v3-turbo",
        "input_audio": {
            "data": base64_audio,
            "format": file_format
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("text")
                else:
                    error_text = await response.text()
                    logger.error(f"STT Error: {response.status} - {error_text}")
                    return None
    except Exception as e:
        logger.exception("Exception during STT transcription:")
        return None
