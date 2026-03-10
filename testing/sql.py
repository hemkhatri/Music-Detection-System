import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="song database"
)

cursor = conn.cursor()
title = "True Love"
youtube_id = "abcd1234"
filepath = "songs/true_love.wav"

cursor.execute(
    "INSERT INTO songs (title, youtube_id, filepath) VALUES (%s,%s,%s)",
    (title, youtube_id, filepath)
)

conn.commit()

song_id = cursor.lastrowid
