import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import mysql.connector
from collections import Counter
import os
from test import generate_fingerprints


# -----------------------------------
# DATABASE CONFIG
# -----------------------------------

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "music_detection"
}


# -----------------------------------
# RECORD AUDIO
# -----------------------------------

def record_audio(duration=10, fs=22050):

    print(f"[*] Recording {duration} seconds... play music now!")

    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    filename = "temp_recorded.wav"

    wavfile.write(filename, fs, recording)

    return filename


# -----------------------------------
# UPLOAD AUDIO FILE
# -----------------------------------

def get_upload_path():

    path = input("Enter full path of audio file: ").strip('"')

    if os.path.exists(path):
        return path

    print("[!] File not found")
    return None


# -----------------------------------
# DATABASE MATCHING
# -----------------------------------

def identify_from_db(recorded_fingerprints):

    try:

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if not recorded_fingerprints:
            return "No fingerprints generated."

        search_hashes = [fp[0] for fp in recorded_fingerprints]

        # Chunk query to avoid huge SQL request
        def chunk_list(lst, size=1000):
            for i in range(0, len(lst), size):
                yield lst[i:i + size]

        db_results = []

        for chunk in chunk_list(search_hashes):

            format_strings = ','.join(['%s'] * len(chunk))

            query = f"""
            SELECT song_id, time_offset, hash
            FROM fingerprints
            WHERE hash IN ({format_strings})
            """

            cursor.execute(query, tuple(chunk))

            db_results.extend(cursor.fetchall())

        if not db_results:
            return "No match found."

        # Map recorded offsets
        recorded_map = {}

        for h, offset in recorded_fingerprints:
            recorded_map.setdefault(h, []).append(offset)

        matches = []

        for row in db_results:

            song_id = row["song_id"]
            db_offset = row["time_offset"]
            h = row["hash"]

            if h in recorded_map:

                for rec_offset in recorded_map[h]:

                    diff = db_offset - rec_offset
                    matches.append((song_id, diff))

        if not matches:
            return "No match alignment found."

        # Find best match
        (song_id, _), count = Counter(matches).most_common(1)[0]

        cursor.execute(
            "SELECT title FROM songs WHERE song_id=%s",
            (song_id,)
        )

        song = cursor.fetchone()

        if song:
            return f"MATCH FOUND: {song['title']} (Confidence: {count})"

        return "Match found but title missing."

    except Exception as e:
        return f"Database Error: {e}"

    finally:

        if 'cursor' in locals():
            cursor.close()

        if 'conn' in locals() and conn.is_connected():
            conn.close()


# -----------------------------------
# MAIN PROGRAM
# -----------------------------------

def main():

    print("=== MUSIC DETECTION SYSTEM ===")

    choice = input("Type R to Record or U to Upload file: ").strip().upper()

    audio_path = None

    if choice == "R":
        audio_path = record_audio()

    elif choice == "U":
        audio_path = get_upload_path()

    else:
        print("Invalid choice")
        return

    if not audio_path:
        return

    print("[*] Generating fingerprints...")

    fingerprints = generate_fingerprints(audio_path)

    print(f"[*] Fingerprints created: {len(fingerprints)}")

    print("[*] Searching database...")

    result = identify_from_db(fingerprints)

    print("\n" + "="*40)
    print(result)
    print("="*40)

    # cleanup
    if choice == "R" and os.path.exists(audio_path):
        os.remove(audio_path)


# -----------------------------------
# RUN
# -----------------------------------

if __name__ == "__main__":
    main()