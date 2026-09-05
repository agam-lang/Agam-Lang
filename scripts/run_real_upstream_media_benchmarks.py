#!/usr/bin/env python3
"""Run genuine real-world upstream media benchmarks on real audio/image files in Linux."""

import os
import subprocess
import time
import math
import wave
import struct
from pathlib import Path

BENCH_DIR = Path("/tmp/real_media_bench")
BENCH_DIR.mkdir(parents=True, exist_ok=True)

# 1. Generate genuine 10-second 44.1kHz Stereo 16-bit WAV Audio File
WAV_PATH = BENCH_DIR / "sample_44k_stereo.wav"
def generate_real_wav():
    sample_rate = 44100
    duration_sec = 10.0
    num_samples = int(sample_rate * duration_sec)
    
    with wave.open(str(WAV_PATH), "w") as wav_file:
        wav_file.setnchannels(2) # Stereo
        wav_file.setsampwidth(2) # 16-bit PCM
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            # 440Hz + 880Hz + 1320Hz musical chord
            left_val = int(16000 * (math.sin(2 * math.pi * 440 * t) + 0.5 * math.sin(2 * math.pi * 880 * t)))
            right_val = int(16000 * (math.sin(2 * math.pi * 554.37 * t) + 0.5 * math.sin(2 * math.pi * 1320 * t)))
            left_val = max(-32767, min(32767, left_val))
            right_val = max(-32767, min(32767, right_val))
            frames += struct.pack("<hh", left_val, right_val)
        wav_file.writeframes(frames)
    print(f"Generated real WAV: {WAV_PATH} ({WAV_PATH.stat().st_size / 1024 / 1024:.2f} MB)")

# 2. Generate genuine 4K Test Image (3840x2160)
IMG_4K_PATH = BENCH_DIR / "sample_4k.png"
def generate_real_image():
    cmd = [
        "gm", "convert",
        "-size", "3840x2160",
        "gradient:blue-gold",
        "-swirl", "180",
        "+noise", "Gaussian",
        str(IMG_4K_PATH)
    ]
    subprocess.run(cmd, check=True)
    print(f"Generated real 4K image: {IMG_4K_PATH} ({IMG_4K_PATH.stat().st_size / 1024 / 1024:.2f} MB)")

def benchmark_cmd(name, cmd_args, runs=3):
    timings = []
    # Warmup
    subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(runs):
        t0 = time.perf_counter()
        res = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        t1 = time.perf_counter()
        if res.returncode != 0:
            print(f"Error running {name}: {res.stderr.decode('utf-8', errors='ignore')}")
            return None
        timings.append((t1 - t0) * 1000.0)
    return min(timings)

def main():
    print("=" * 95)
    print("REAL UPSTREAM MEDIA CODEC & GRAPHICS BENCHMARKS (MEASURED ON REAL FILES)")
    print("=" * 95)

    generate_real_wav()
    generate_real_image()

    print("\n" + "-" * 95)
    print(f"{'Benchmark Target':<40} | {'Execution Setting / Command':<30} | {'Throughput / Time'}")
    print("-" * 95)

    # 1. FLAC Audio Encoding (WAV -> FLAC across presets)
    flac_out = BENCH_DIR / "output.flac"
    for preset in [0, 5, 8]:
        t = benchmark_cmd(f"FLAC (Preset -{preset})", ["flac", "-f", f"-{preset}", str(WAV_PATH), "-o", str(flac_out)])
        rate = (WAV_PATH.stat().st_size / 1024 / 1024) / (t / 1000.0)
        print(f"{'FLAC Audio Encode (libFLAC upstream)':<40} | {f'flac -{preset} (16-bit 44.1kHz)':<30} | {t:.2f} ms ({rate:.1f} MB/s)")

    # 2. LAME MP3 Audio Encoding (WAV -> MP3)
    mp3_out = BENCH_DIR / "output.mp3"
    t_mp3 = benchmark_cmd("LAME MP3 (V0)", ["lame", "-V0", str(WAV_PATH), str(mp3_out)])
    rate_mp3 = (WAV_PATH.stat().st_size / 1024 / 1024) / (t_mp3 / 1000.0)
    print(f"{'LAME MP3 Encode (libmp3lame)':<40} | {'lame -V0 (High Quality VBR)':<30} | {t_mp3:.2f} ms ({rate_mp3:.1f} MB/s)")

    # 3. WebP Image Encoding (cwebp on 4K image)
    for q in [100]:
        webp_lossy = BENCH_DIR / f"output_q{q}.webp"
        t_webp = benchmark_cmd("cwebp (Lossy Q100)", ["cwebp", "-q", str(q), str(IMG_4K_PATH), "-o", str(webp_lossy)])
        print(f"{'WebP 4K Image Encode (libwebp)':<40} | {f'cwebp -q {q} (4K 3840x2160)':<30} | {t_webp:.2f} ms")

        webp_lossless = BENCH_DIR / f"output_lossless_q{q}.webp"
        t_lossless = benchmark_cmd("cwebp (Lossless Q100)", ["cwebp", "-lossless", "-q", str(q), "-m", "6", str(IMG_4K_PATH), "-o", str(webp_lossless)])
        print(f"{'WebP 4K Image Encode (libwebp)':<40} | {'cwebp -lossless -q 100 -m 6':<30} | {t_lossless:.2f} ms")

    # 4. GraphicsMagick Operations on 4K Image
    gm_ops = [
        ("Swirl (180 deg)", ["gm", "convert", str(IMG_4K_PATH), "-swirl", "180", str(BENCH_DIR / "gm_swirl.png")]),
        ("Rotate (90 deg)", ["gm", "convert", str(IMG_4K_PATH), "-rotate", "90", str(BENCH_DIR / "gm_rotate.png")]),
        ("Sharpen (3x3 Gaussian)", ["gm", "convert", str(IMG_4K_PATH), "-sharpen", "1.0", str(BENCH_DIR / "gm_sharpen.png")]),
        ("Enhance Filter", ["gm", "convert", str(IMG_4K_PATH), "-enhance", str(BENCH_DIR / "gm_enhance.png")]),
        ("Resize (50% to 1080p)", ["gm", "convert", str(IMG_4K_PATH), "-resize", "50%", str(BENCH_DIR / "gm_resize.png")]),
        ("Gaussian Noise Addition", ["gm", "convert", str(IMG_4K_PATH), "+noise", "Gaussian", str(BENCH_DIR / "gm_noise.png")]),
        ("HWB Color Space Conversion", ["gm", "convert", str(IMG_4K_PATH), "-colorspace", "HWB", str(BENCH_DIR / "gm_hwb.png")]),
    ]
    for op_name, cmd in gm_ops:
        t_gm = benchmark_cmd(f"GraphicsMagick {op_name}", cmd)
        print(f"{f'GraphicsMagick {op_name}':<40} | {'4K Image (3840x2160)':<30} | {t_gm:.2f} ms")

    print("=" * 95)

if __name__ == "__main__":
    main()
