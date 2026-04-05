import mysql.connector
from collections import Counter

db_config = {
    "host": "localhost",
    "user": "root", 
    "password": "",
    "database": "music_detection"
}

def identify_music(recorded_fingerprints):
    """
    recorded_fingerprints: List of (hash, offset) tuples from your recording.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        all_matches = []
        
        # 1. Get the list of hashes to search for
        hashes = [f[0] for f in recorded_fingerprints]
        if not hashes:
            return "No fingerprints provided."

        # 2. Batch search using your exact column names
        format_strings = ','.join(['%s'] * len(hashes))
        query = f"""
            SELECT song_id, time_offset, hash 
            FROM fingerprints 
            WHERE hash IN ({format_strings})
        """
        cursor.execute(query, tuple(hashes))
        db_results = cursor.fetchall()

        # Map recorded offsets to their hashes for easy comparison
        recorded_map = {h: off for h, off in recorded_fingerprints}

        # 3. Calculate the Time Difference (Alignment)
        for row in db_results:
            s_id = row['song_id']
            db_off = row['time_offset']  # Using your column name
            rec_off = recorded_map[row['hash']]
            
            diff = db_off - rec_off
            all_matches.append((s_id, diff))

        if not all_matches:
            return "No match found in the database."

        # 4. Find the most common (song_id, diff) pair
        best_match, count = Counter(all_matches).most_common(1)[0]
        match_song_id, _ = best_match

        # 5. Fetch the Title from the songs table
        # Assuming your songs table uses 'song_id' as the primary key
        cursor.execute("SELECT title FROM songs WHERE song_id = %s", (match_song_id,))
        song = cursor.fetchone()

        if song:
            return f"MATCH FOUND: {song['title']} (Confidence: {count} aligned hashes)"
        return "Match found, but song details are missing."

    except mysql.connector.Error as err:
        return f"Database Error: {err}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# --- Example of how to call it ---
recorded_data = [('96407d138c32995d7cb7', 142), ('6bad8195fa55b647540c', 142), ('05c8a6581c393f98d300', 167)]
print(identify_music(recorded_data))
