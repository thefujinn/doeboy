import lyricsgenius as genius
from googletrans import Translator
import pymongo
import os

MONGODB_URI = os.environ['MONGODB_URI']
genius_api = genius.Genius(os.environ['GENIUS_TOKEN'])
mongo_client = pymongo.MongoClient(MONGODB_URI)
songs_db = mongo_client[os.environ['MONGO_DB_NAME']]

translator = Translator()

ru = songs_db["ru_songs"]
en = songs_db["en_songs"]
artists = ["travis scott", "6ix9ine", "juice WRLD", "tyga", "XXXTENTACION"]

for a in artists:
    artist = genius_api.search_artist(a, max_songs=150)
    for song in artist.songs:
        print("adding " + song.artist + " | " + song.title)
        try:
            t = translator.translate(song.lyrics, src='en', dest='ru')
            en.insert_one({ "author_name": song.artist, "song_name": song.title, "song_id": song._id, "text": song.lyrics })
            ru.insert_one({ "author_name": song.artist, "song_name": song.title, "song_id": song._id, "text": t.text })
        except:
            print("Error while translating")
