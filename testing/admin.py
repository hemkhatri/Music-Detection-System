import yt_dlp
import mysql.connector
import os
from test import generate_fingerprints


# -----------------------------------
# DATABASE CONNECTION
# -----------------------------------

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "music_detection"
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# -----------------------------------
# DOWNLOAD AUDIO FROM YOUTUBE
# -----------------------------------

def download_audio(url):

    os.makedirs("songs", exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
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

def insert_song(cursor, title, youtube_id):

    cursor.execute(
        "INSERT IGNORE INTO songs (title, youtube_id) VALUES (%s,%s)",
        (title, youtube_id)
    )

    if cursor.lastrowid == 0:
        cursor.execute(
            "SELECT song_id FROM songs WHERE youtube_id=%s",
            (youtube_id,)
        )
        return cursor.fetchone()[0]

    return cursor.lastrowid


# -----------------------------------
# STORE FINGERPRINTS
# -----------------------------------

def insert_fingerprints(cursor, song_id, fingerprints):

    data = [(h, song_id, t) for h, t in fingerprints]

    cursor.executemany(
        "INSERT IGNORE INTO fingerprints (hash, song_id, time_offset) VALUES (%s,%s,%s)",
        data
    )


# -----------------------------------
# MAIN PROCESS
# -----------------------------------

def process_song(url):

    print("[*] Downloading audio...")
    title, youtube_id, filepath = download_audio(url)
    print(f"[+] Downloaded: {title}")

    try:

        print("[*] Generating fingerprints...")
        fingerprints = generate_fingerprints(filepath)
        print(f"[+] Fingerprints generated: {len(fingerprints)}")

        conn = get_connection()
        cursor = conn.cursor()

        print("[*] Storing song in database...")
        song_id = insert_song(cursor, title, youtube_id)

        print("[*] Storing fingerprints...")
        insert_fingerprints(cursor, song_id, fingerprints)

        conn.commit()

        print("[✓] Song stored successfully.")

    finally:

        if 'cursor' in locals():
            cursor.close()

        if 'conn' in locals():
            conn.close()

        if os.path.exists(filepath):
            os.remove(filepath)
            print("[*] Temporary audio deleted.")


# -----------------------------------
# RUN SCRIPT
# -----------------------------------

if __name__ == "__main__":

    print("=== ADMIN PANEL ===")

    url = input("Enter YouTube URL: ").strip()

    process_song(url)