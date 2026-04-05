import librosa
import numpy as np
import hashlib
from scipy.ndimage import maximum_filter


# -----------------------------------
# HASH FUNCTION
# -----------------------------------
def hash_fingerprint(fp):
    """
    Convert fingerprint tuple into a short SHA1 hash
    """
    return hashlib.sha1(str(fp).encode()).hexdigest()[0:20]


# -----------------------------------
# FINGERPRINT GENERATOR
# -----------------------------------
def generate_fingerprints(audio_file):

    # 1. Load Audio
    y, sr = librosa.load(audio_file, sr=22050, mono=True)

    # 2. Create Spectrogram
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=2048))
    S_db = librosa.amplitude_to_db(S, ref=np.max)

    # 3. Peak Detection
    neighborhood_size = 30
    local_max = maximum_filter(S_db, size=neighborhood_size) == S_db

    threshold = np.percentile(S_db, 97)

    detected_peaks = np.argwhere(local_max & (S_db >= threshold))

    # Convert peaks
    peaks = [(int(freq), int(time)) for freq, time in detected_peaks]

    # Sort by time
    peaks.sort(key=lambda x: x[1])

    # 4. Limit peaks per time frame
    max_peaks_per_frame = 5
    filtered_peaks_dict = {}

    for freq, time in peaks:
        if time not in filtered_peaks_dict:
            filtered_peaks_dict[time] = []

        if len(filtered_peaks_dict[time]) < max_peaks_per_frame:
            filtered_peaks_dict[time].append((freq, time))

    peaks = [p for sublist in filtered_peaks_dict.values() for p in sublist]

    # 5. Fingerprint Pairing
    fingerprints = []
    fan_value = 3

    for i in range(len(peaks)):
        freq1, t1 = peaks[i]

        for j in range(1, fan_value + 1):

            if i + j < len(peaks):

                freq2, t2 = peaks[i + j]
                delta_t = t2 - t1

                if 0 < delta_t <= 200:

                    fingerprint = (freq1, freq2, delta_t)
                    h = hash_fingerprint(fingerprint)

                    fingerprints.append((h, t1))

    return fingerprints