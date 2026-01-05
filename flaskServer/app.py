import numpy as np
import sounddevice as sd
import tensorflow as tf
import tensorflow_hub as hub
import queue
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import time


# -----------------------------
# Load YAMNet uvicorn app:app --host 0.0.0.0 --port 8000 --reload
# -----------------------------
print("[INFO] Loading YAMNet model...")
yamnet = hub.load("https://tfhub.dev/google/yamnet/1")

class_map_path = tf.keras.utils.get_file(
    "yamnet_class_map.csv",
    "https://storage.googleapis.com/audioset/yamnet/yamnet_class_map.csv"
)
df = pd.read_csv(class_map_path)
class_names = df['display_name'].tolist()

# -----------------------------
# Siren keywords
# -----------------------------
SIREN_KEYWORDS = [
    "siren",
    "police car (siren)",
    "ambulance (siren)",
    "fire engine, fire truck (siren)",
    "emergency vehicle"
]

# -----------------------------
# Audio settings
# -----------------------------
SAMPLE_RATE = 16000
BLOCK_DURATION = 0.5
BLOCK_SIZE = int(SAMPLE_RATE * BLOCK_DURATION)
audio_queue = queue.Queue()
latest_data = {}  # Shared latest detection

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Helper functions
# -----------------------------
def classify_siren(mean_scores):
    # Focus only on siren vs normal traffic
    siren_score = 0.0
    normal_score = 0.0
    for idx, name in enumerate(class_names):
        lname = name.lower()
        if any(k in lname for k in SIREN_KEYWORDS):
            siren_score += mean_scores[idx]
        else:
            normal_score += mean_scores[idx]

    # Decide category based on higher score and threshold
    if siren_score > normal_score and siren_score > 0.2:  # 0.2 threshold reduces false positives
        return "SIREN", siren_score
    else:
        return "NORMAL TRAFFIC", normal_score

def get_dominant_frequency(audio, sr):
    audio = audio * np.hanning(len(audio))
    fft = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(len(audio), d=1/sr)
    magnitude = np.abs(fft)
    return freqs[np.argmax(magnitude)]

# -----------------------------
# Audio callback
# -----------------------------
def audio_callback(indata, frames, time_data, status):
    if status:
        print(status)
    audio_queue.put(indata.copy().flatten())

# -----------------------------
# Audio processing thread
# -----------------------------
def start_audio_stream():
    global latest_data
    audio_buffer = np.array([], dtype=np.float32)
    with sd.InputStream(channels=1, samplerate=SAMPLE_RATE,
                        blocksize=BLOCK_SIZE, callback=audio_callback):
        print("[INFO] Microphone stream started...")
        while True:
            block = audio_queue.get()
            audio_buffer = np.concatenate([audio_buffer, block])
            if len(audio_buffer) > SAMPLE_RATE:
                audio_buffer = audio_buffer[-SAMPLE_RATE:]

            if len(audio_buffer) >= SAMPLE_RATE:
                scores, embeddings, spectrogram = yamnet(audio_buffer)
                mean_scores = np.mean(scores, axis=0)

                category, confidence = classify_siren(mean_scores)

                top_idx = np.argmax(mean_scores)
                top_class = class_names[top_idx]

                dominant_freq = get_dominant_frequency(audio_buffer, SAMPLE_RATE)
                SPEED_OF_SOUND = 343.0
                wavelength = SPEED_OF_SOUND / dominant_freq if dominant_freq > 0 else 0

                latest_data = {
                    "top_class": top_class,
                    "confidence": round(float(confidence), 2),
                    "category": category,
                    "dominant_freq": round(float(dominant_freq), 1),
                    "wavelength": round(float(wavelength), 2)
                }

# -----------------------------
# REST endpoint
# -----------------------------
@app.get("/latest")
def get_latest_data():
    return latest_data

# -----------------------------
# Start audio thread
# -----------------------------
threading.Thread(target=start_audio_stream, daemon=True).start()

# -----------------------------
# Run with:
# uvicorn server:app --host 0.0.0.0 --port 8000
# -----------------------------
print("[INFO] Server running... Press Ctrl+C to stop.")
