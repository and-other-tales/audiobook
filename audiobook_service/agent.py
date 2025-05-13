import io
import json
import wave
from typing import List, Dict

from agents import Agent
from agents.run import Runner
from agents.voice.models.openai_model_provider import OpenAIVoiceModelProvider
from agents.voice.model import TTSModelSettings

from .file_parser import parse_file

async def segment_chapter(chapter_text: str) -> List[Dict]:
    """
    Use a completions agent to split the chapter into segments, detect tone and voice settings.
    """
    agent = Agent(
        name="Segmenter",
        instructions=(
            "You are a skilled audiobook narrator assistant. "
            "Given a chapter of a novel, perform the following steps:\n"
            "1. Split the chapter into segments not exceeding 1000 words each at sentence boundaries.\n"
            "2. For each segment, identify if it is narrative or dialogue. "
            "If dialogue, identify the speaker's name, and infer the speaker's gender: male or female.\n"
            "3. For each segment, determine the intended tone (e.g., calm, tense, joyful) and pacing.\n"
            "4. Assign to each segment:\n"
            "   - \"voice_name\": \"Ballad\" for male, \"Coral\" for female.\n"
            "   - \"speed\": 0.85 for male, 0.9 for female.\n"
            "   - \"instructions\": \"Please read in a British accent with a {tone} tone and {pacing} pacing.\"\n"
            "5. Output a JSON array of segments. Each segment must be an object with keys:\n"
            "   \"text\", \"voice_name\", \"speed\", \"instructions\".\n"
            "Return only the JSON array with no additional text."
        ),
        model="gpt-4",
    )
    result = await Runner.run(agent, chapter_text)
    try:
        segments = json.loads(result.final_output)
    except Exception as e:
        raise ValueError(f"Segmenter agent returned invalid JSON: {e}")
    return segments

async def synthesize_segments(segments: List[Dict]) -> bytes:
    """
    Use the OpenAI TTS API to synthesize each segment and return combined WAV bytes.
    """
    provider = OpenAIVoiceModelProvider()
    tts_model = provider.get_tts_model("gpt-4o-mini-tts")
    buf = io.BytesIO()
    wf = wave.open(buf, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(2)  # int16 = 2 bytes
    wf.setframerate(24000)
    for segment in segments:
        text = segment.get("text", "")
        voice_name = segment.get("voice_name", "").lower()
        speed = segment.get("speed")
        instructions = segment.get("instructions", "")
        settings = TTSModelSettings(
            voice=voice_name,
            speed=speed,
            instructions=instructions,
        )
        async for chunk in tts_model.run(text, settings):
            wf.writeframes(chunk)
    wf.close()
    return buf.getvalue()

async def process_manuscript(contents: bytes, filename: str) -> bytes:
    """
    Parse the manuscript, process each chapter, and bundle WAVs into a ZIP archive.
    """
    chapters = parse_file(contents, filename)
    import zipfile
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        for idx, (title, text) in enumerate(chapters):
            segments = await segment_chapter(text)
            wav_data = await synthesize_segments(segments)
            fname = f"chapter_{idx+1}.wav"
            zf.writestr(fname, wav_data)
    zip_buf.seek(0)
    return zip_buf.getvalue()