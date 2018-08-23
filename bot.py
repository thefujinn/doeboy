from telegram.ext import Updater, CommandHandler
import markovify
import lyricsgenius as genius
import os
from googletrans import Translator
import pymongo
import logging
import timber


logger = logging.getLogger(__name__)
timber_handler = timber.TimberHandler(api_key=os.environ['TIMBER_TOKEN'])
logger.addHandler(timber_handler)
logger.setLevel(logging.INFO)

class Model:
    def __init__(self, db, collection_name, author_name=""):
        self.collection = db[collection_name]
        self.query = {"author_name": author_name} if (len(author_name) > 0) else {}
        self.update_model()

    def add_song(self, author_name, song_name, song_id, text):
        if self.collection.find({"song_id": song_id}).count() == 0:
            self.collection.insert_one({
                "author_name": author_name,
                "song_name": song_name,
                "song_id": song_id,
                "text": text
            })

    def update_model(self):
        source = 'Doe boy'
        data = self.collection.find(self.query, {"text": 1})
        for t in data:
            stripped = t['text'].replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "").replace('"', "")
            source += stripped + "\n"
        self.model = markovify.Text(source)

    def get_quote(self, size=None):
        if size is None:
            return self.model.make_sentence()
        else:
            return self.model.make_short_sentence(size)


MONGO_DB_NAME = os.environ['MONGO_DB_NAME']
genius_api = genius.Genius(os.environ['GENIUS_TOKEN'])
updater = Updater(os.environ['TELEGRAM_TOKEN'])
mongo_client = pymongo.MongoClient(os.environ['MONGODB_URI'])
songs_db = mongo_client[MONGO_DB_NAME]

translator = Translator()

ru_model = Model(songs_db, "ru_songs")
en_model = Model(songs_db, "en_songs")


def log_request(user, command, args):
    logger.info(user['username'] + ' > ' + command + ': ' + args)

def get_model(args):
    return en_model if (len(args) > 0) and (args[0] == "en") else ru_model


def get_quote(bot, update, args):
    log_request(update.message.from_user, 'getquote', " ".join(args))
    update.message.reply_text(get_model(args).get_quote(140))


def get_long_quote(bot, update, args):
    log_request(update.message.from_user, 'getstory', " ".join(args))
    update.message.reply_text(get_model(args).get_quote())


def translate_song(bot, update, args):
    search_term = " ".join(args)
    log_request(update.message.from_user, 'translate', search_term)
    if not search_term:
        update.message.reply_text("Give me the name, son")
    else:
        song = genius_api.search_song(search_term)
        t = translator.translate(song.lyrics, src='en', dest='ru')
        ru_model.add_song(song.artist, song.title, song._id, t.text)
        en_model.add_song(song.artist, song.title, song._id, song.lyrics)
        update.message.reply_text(t.text)


updater.dispatcher.add_handler(CommandHandler('getquote', get_quote, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('getstory', get_long_quote, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('translate', translate_song, pass_args=True))

updater.start_polling()
updater.idle()
