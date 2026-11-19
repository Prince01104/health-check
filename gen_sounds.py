"""Makes the 4 calming sounds in assets/sounds (30 seconds each, they loop). Run once: python gen_sounds.py"""
import wave
from pathlib import Path

import numpy as np

SR = 16000
SECONDS = 30
OUT = Path(__file__).parent / "assets" / "sounds"
rng = np.random.default_rng(7)
t = np.arange(SR * SECONDS) / SR


def smooth(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def finish(x, peak=0.5):
    x = x - x.mean()
    x = x / (np.abs(x).max() + 1e-9) * peak
    fade = SR  # 1 second fade in and out so the loop has no click
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    return x


def save(name, x):
    OUT.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


white = rng.normal(size=t.size)

# soft rain: bright noise with a slow swell
rain = (white - smooth(white, 40)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t))
save("rain.wav", finish(rain))

# ocean: low noise swelling every 9 seconds
ocean = smooth(white, 60) * (0.25 + 0.75 * np.sin(np.pi * t / 9.0) ** 2)
save("ocean.wav", finish(ocean))

# deep hum: three low tones with a slow tremolo
hum = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((82.4, 1.0), (123.5, 0.6), (164.8, 0.4)))
hum = hum * (0.85 + 0.15 * np.sin(2 * np.pi * 0.1 * t))
save("hum.wav", finish(hum, 0.35))

# brown noise
brown = np.cumsum(white)
brown = brown - smooth(brown, SR)  # remove slow drift
save("brown.wav", finish(brown))
print("done")
