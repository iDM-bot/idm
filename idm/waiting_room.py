import discord
from queue import Queue
from discord.ext import commands
import time
import asyncio
from _datetime import date
import datetime
from config import db_connection_string, server_time, bot_name


class WaitingRoom(commands.Cog):
    """Waiting room before being matched with an opponent"""

  # Maximum time a player can be in the queue.
    def __init__(self, context):
        self.__context = context
        self.__client = discord.Client()
        self.__player_queue = Queue()
        self.__players_in_queue = set()
        self.__players = list()
        self.__MAX_WAITROOM_TIME = 120
        self.__is_dm_active = False

    def add_player_to_queue(self, player):
        if not player.get_id() in self.__players_in_queue:
            self.__player_queue.put(player)
            self.__players_in_queue.add(player.get_id())

            if player.get_wait_time() is None:
                player.start_timer()

    async def get_player_from_queue(self):
        next_player = self.__player_queue.get()
        self.__players_in_queue.remove(next_player.get_id())

        return next_player
  
    def is_player_waiting(self, player_id):
        return player_id in self.__players_in_queue
  
    def count_players_waiting(self):
        return len(self.__players_in_queue)

    def get_max_timeout(self):
        return self.__MAX_WAITROOM_TIME

    async def run_timeout_routine(self):
        while True:
            if not self.__is_dm_active:
                player_list = list(self.__player_queue.queue)
                self.__player_queue = Queue()
                self.__players_in_queue = set()

                for player in player_list:
                    if player.get_wait_time() < self.__MAX_WAITROOM_TIME:
                        self.add_player_to_queue(player)
                    else:
                        await self.__context.send(f'{bot_name} Removing {player.get_discord_display_name()} from the waiting room, they have been waiting {player.get_wait_time():.0f} seconds.')
            
            await asyncio.sleep(1)

        return

def setup(client):
    client.add_cog(WaitingRoom(None))
