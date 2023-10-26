import mysql.connector
import json
import glob

with open("connection_data.json", "r") as f:
    db_credentials = json.load(f)
        
db = mysql.connector.connect(**db_credentials)
db_cur = db.cursor()

for file in ["Album1", "Album2", "Yet Another Album"]:
    print(file)
    db_cur.execute("INSERT INTO albums (albumName) VALUES (%s);", (file,))
    db.commit()