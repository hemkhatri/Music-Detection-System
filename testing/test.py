import yt_dlp
import librosa
import numpy as np
import hashlib
import mysql.connector
from scipy.ndimage import maximum_filter
import os


# -----------------------------------
# DATABASE CONNECTION
# -----------------------------------

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="music_detection"
)

cursor = conn.cursor()


# -----------------------------------
# HASH FUNCTION
# -----------------------------------

def hash_fingerprint(fp):
    return hashlib.sha1(str(fp).encode()).hexdigest()[0:20]


# -----------------------------------
# FINGERPRINT GENERATOR
# -----------------------------------
def generate_fingerprints(audio_file):
    # 1. Load audio
    y, sr = librosa.load(audio_file, sr=22050)

    # 2. Spectrogram (Balanced settings)
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=2048))
    S_db = librosa.amplitude_to_db(S, ref=np.max)

    # 3. Peak Detection
    neighborhood_size = 30  # Increased for better peak distribution
    local_max = maximum_filter(S_db, size=neighborhood_size) == S_db

    threshold = np.percentile(S_db, 97)
    detected_peaks = np.argwhere(local_max & (S_db >= threshold))

    # Convert to list and sort by time
    peaks = [(int(freq), int(time)) for freq, time in detected_peaks]
    peaks.sort(key=lambda x: x[1])

    # 4. Limit peaks per time frame (New Optimization)
    max_peaks_per_frame = 5
    filtered_peaks_dict = {}

    for freq, time in peaks:
        if time not in filtered_peaks_dict:
            filtered_peaks_dict[time] = []
        if len(filtered_peaks_dict[time]) < max_peaks_per_frame:
            filtered_peaks_dict[time].append((freq, time))

    # Flatten back to a list
    peaks = [p for sublist in filtered_peaks_dict.values() for p in sublist]

    # 5. Fingerprinting / Pairing (Reduced Fan-out)
    fingerprints = []
    fan_value = 3  # Reduced from 5 to 3

    for i in range(len(peaks)):
        freq1, t1 = peaks[i]
        for j in range(1, fan_value + 1):
            if i + j < len(peaks):
                freq2, t2 = peaks[i + j]
                delta_t = t2 - t1

                # Constraints on pairing
                if 0 < delta_t <= 200:
                    fingerprint = (freq1, freq2, delta_t)
                    h = hash_fingerprint(fingerprint)
                    fingerprints.append((h, t1))

    return fingerprints



# -----------------------------------
# DOWNLOAD AUDIO FROM YOUTUBE
# -----------------------------------

def download_audio(url):

    ydl_opts = {
        "format": "bestaudio/best",
        "ffmpeg_location": r"E:\Downloads\Compressed\ffmpeg-2026-03-09-git-9b7439c31b-full_build\ffmpeg-2026-03-09-git-9b7439c31b-full_build\bin",
        "outtmpl": "songs/%(title)s[%(id)s].%(ext)s",
        "restrictfilenames": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav"
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        title = info["title"]
        youtube_id = info["id"]

        filename = ydl.prepare_filename(info)
        filename = os.path.splitext(filename)[0] + ".wav"

        return title, youtube_id, filename


# -----------------------------------
# STORE SONG
# -----------------------------------

def insert_song(title, youtube_id, filepath):
    # Removed 'filepath' from the query because the column doesn't exist anymore
    cursor.execute(
        "INSERT INTO songs (title, youtube_id) VALUES (%s, %s)",
        (title, youtube_id)
    )
    conn.commit()
    return cursor.lastrowid



# -----------------------------------
# STORE FINGERPRINTS
# -----------------------------------

def insert_fingerprints(song_id, fingerprints):

    data = []

    for h, t in fingerprints:
        data.append((h, song_id, t))

    cursor.executemany(
        "INSERT INTO fingerprints (hash, song_id, time_offset) VALUES (%s,%s,%s)",
        data
    )

    conn.commit()


# -----------------------------------
# MAIN PIPELINE
# -----------------------------------

def process_song(url):
    print("Downloading audio...")
    title, youtube_id, filepath = download_audio(url)
    print("Audio downloaded:", filepath)

    try:
        print("Generating fingerprints...")
        fingerprints = generate_fingerprints(filepath)
        print("Fingerprints generated:", len(fingerprints))

        print("Storing song in database...")
        song_id = insert_song(title, youtube_id, filepath)
        print("Song ID:", song_id)

        print("Storing fingerprints...")
        insert_fingerprints(song_id, fingerprints)
        print("Done. Song stored successfully.")

    finally:
        # This deletes the file even if the fingerprinting fails
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Temporary file deleted: {filepath}")


# -----------------------------------
# RUN
# -----------------------------------

url = "https://www.youtube.com/watch?v=XcEC2q4CotY"

process_song(url)