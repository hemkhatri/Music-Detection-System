import os
from flask import Flask, render_template, request, jsonify
import mysql.connector
from collections import Counter
from test import generate_fingerprints

app = Flask(__name__)

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
# DATABASE MATCHING 
# -----------------------------------
def identify_from_db(recorded_fingerprints):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if not recorded_fingerprints:
            return {"match": False, "message": "No fingerprints generated."}

        search_hashes = [fp[0] for fp in recorded_fingerprints]

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
            return {"match": False, "message": "No match found."}

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
            return {"match": False, "message": "No match alignment found."}

        (song_id, _), count = Counter(matches).most_common(1)[0]
        
        # We grab the youtube_id here now!
        cursor.execute("SELECT title, youtube_id FROM songs WHERE song_id=%s", (song_id,))
        song = cursor.fetchone()

        if song:
            return {
                "match": True,
                "title": song['title'],
                "youtube_id": song['youtube_id'],
                "confidence": count,
                "message": f"MATCH FOUND: {song['title']} (Confidence: {count})"
            }

        return {"match": False, "message": "Match found but title missing."}

    except Exception as e:
        return {"match": False, "message": f"Database Error: {e}"}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# -----------------------------------
# WEB ROUTES
# -----------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({"match": False, "message": "No audio file received."}), 400
    
    audio_file = request.files['audio']
    temp_path = "temp_web_upload.wav"
    audio_file.save(temp_path)
    
    try:
        fingerprints = generate_fingerprints(temp_path)
        result_data = identify_from_db(fingerprints)
    except Exception as e:
        result_data = {"match": False, "message": f"Processing Error: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return jsonify(result_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)