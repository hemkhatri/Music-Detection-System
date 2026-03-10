import librosa
import numpy as np
import hashlib
from scipy.ndimage import maximum_filter


# -----------------------------
# Hash function
# -----------------------------
def hash_fingerprint(fp):
    return hashlib.sha1(str(fp).encode()).hexdigest()[0:20]


# -----------------------------
# Fingerprint generator
# -----------------------------
def generate_fingerprints(audio_file):

    # Load audio
    y, sr = librosa.load(audio_file, sr=22050)

    # Create spectrogram
    S = np.abs(librosa.stft(y))

    # Convert to decibel scale
    S_db = librosa.amplitude_to_db(S, ref=np.max)

    # Detect local peaks
    neighborhood_size = 20
    local_max = maximum_filter(S_db, size=neighborhood_size) == S_db

    threshold = np.percentile(S_db, 90)

    detected_peaks = np.argwhere(local_max & (S_db >= threshold))

    # Each peak = (frequency_bin, time_frame)
    peaks = [(int(freq), int(time)) for freq, time in detected_peaks]

    # Sort peaks by time
    peaks.sort(key=lambda x: x[1])

    fingerprints = []

    fan_value = 5   # number of peak pairs

    for i in range(len(peaks)):

        freq1, t1 = peaks[i]

        for j in range(1, fan_value):

            if i + j < len(peaks):

                freq2, t2 = peaks[i + j]

                delta_t = t2 - t1

                if 0 < delta_t <= 200:

                    fingerprint = (freq1, freq2, delta_t)

                    h = hash_fingerprint(fingerprint)

                    fingerprints.append((h, t1))

    return fingerprints


# -----------------------------
# Test the fingerprint system
# -----------------------------
audio_file = "songs/GOli - True Love  Nepali Love song  2021 (Official Audio) - GOli.mp3"

fp = generate_fingerprints(audio_file)

print("Total fingerprints:", len(fp))

print("\nFirst 10 fingerprints:")
for item in fp:
    print(item)