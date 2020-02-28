import datetime
import time
import os

server_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

bot_description = 'iDM for Discord'
discord_game_played = f'Duel Arena'

discord_token = os.environ['IDM_DISCORD_TOKEN']

db_connection_string = f'mongodb+srv://{os.environ["IDM_MONGO_PASSWORD"]}@idm-koiuh.gcp.mongodb.net/test'

bot_name = f'iDM'

