# ai_pipeline.py
"""
AI Processing Pipeline for Educational Video Generator
- Text Enhancement (GPT-2/Llama)
- Text-to-Speech (Coqui TTS)
- Image Generation (Stable Diffusion XL)
- Video Assembly (FFmpeg)
"""

from transformers import pipeline as hf_pipeline, AutoTokenizer, AutoModelForCausalLM
import requests
from diffusers import StableDiffusionPipeline
import subprocess
import os
import uuid
from typing import List

# --- Text Enhancement ---
def enhance_text(input_text: str, model_name: str = "gpt2") -> str:
    """Enhance educational text using GPT-2 or Llama."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    generator = hf_pipeline("text-generation", model=model, tokenizer=tokenizer)
    result = generator(input_text, max_length=512, num_return_sequences=1)
    return result[0]['generated_text']

# --- Text-to-Speech ---

# --- ElevenLabs TTS API ---
def generate_audio(text: str, voice: str = "Rachel", out_path: str = "output.mp3", speed: float = 1.0, api_key: str = None) -> str:
    """Generate speech audio from text using ElevenLabs TTS API."""
    if api_key is None:
        api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ElevenLabs API key not set. Set ELEVENLABS_API_KEY as env variable or pass as argument.")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5, "style": 0.5, "use_speaker_boost": True},
        "model_id": "eleven_multilingual_v2"
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"TTS API error: {response.status_code} {response.text}")
    with open(out_path, "wb") as f:
        f.write(response.content)
    return out_path

# --- Image Generation ---
def generate_images(prompts: List[str], out_dir: str, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0") -> List[str]:
    """Generate images using Stable Diffusion XL."""
    pipe = StableDiffusionPipeline.from_pretrained(model_id)
    os.makedirs(out_dir, exist_ok=True)
    image_paths = []
    for i, prompt in enumerate(prompts):
        image = pipe(prompt).images[0]
        img_path = os.path.join(out_dir, f"img_{i+1}.png")
        image.save(img_path)
        image_paths.append(img_path)
    return image_paths

# --- Video Assembly ---
def assemble_video(image_paths: List[str], audio_path: str, out_path: str = "output.mp4", duration: int = 60, music_path: str = None) -> str:
    """Combine images and audio into a video using FFmpeg."""
    # Create video from images
    img_pattern = os.path.join(os.path.dirname(image_paths[0]), "img_%d.png")
    video_tmp = out_path.replace('.mp4', '_tmp.mp4')
    img_count = len(image_paths)
    img_duration = duration // img_count
    ffmpeg_img_cmd = [
        "ffmpeg", "-y", "-framerate", str(1/img_duration), "-i", img_pattern,
        "-c:v", "libx264", "-r", "30", "-pix_fmt", "yuv420p", video_tmp
    ]
    subprocess.run(ffmpeg_img_cmd, check=True)
    # Add audio
    ffmpeg_audio_cmd = [
        "ffmpeg", "-y", "-i", video_tmp, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-shortest", out_path
    ]
    subprocess.run(ffmpeg_audio_cmd, check=True)
    # Optionally add background music (not implemented here)
    os.remove(video_tmp)
    return out_path

# --- Pipeline Orchestration ---
def process_video_pipeline(
    text: str,
    template: str,
    voice_type: str,
    user_id: str,
    out_dir: str = "static/videos",
    duration: int = 60,
    elevenlabs_api_key: str = None
) -> dict:
    """Full pipeline: enhance text, generate images/audio, assemble video."""
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(out_dir, job_id)
    os.makedirs(job_dir, exist_ok=True)
    # 1. Enhance text
    enhanced_text = enhance_text(text)
    # 2. Extract prompts (simple split for now)
    prompts = [f"{template} educational image: {line.strip()}" for line in enhanced_text.split('.') if line.strip()][:3]
    # 3. Generate images
    image_paths = generate_images(prompts, job_dir)
    # 4. Generate audio
    audio_path = os.path.join(job_dir, "audio.mp3")
    generate_audio(enhanced_text, voice=voice_type, out_path=audio_path, api_key=elevenlabs_api_key)
    # 5. Assemble video
    video_path = os.path.join(job_dir, "video.mp4")
    assemble_video(image_paths, audio_path, out_path=video_path, duration=duration)
    return {
        "job_id": job_id,
        "video_path": video_path,
        "image_paths": image_paths,
        "audio_path": audio_path,
        "prompts": prompts,
        "enhanced_text": enhanced_text
    }
