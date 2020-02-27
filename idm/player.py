import time
import discord
from discord.ext import commands
import math as m

class Player(commands.Cog):

    def __init__(self, discord_user, discord_display_name):
        self.client = discord.Client()
        self.__id = None
        self.__money = None
        self.__wins = None
        self.__losses = None
        self.__items = set()
        self.__start_time = None
        self.__discord_user = discord_user
        self.__discord_display_name = discord_display_name
        self.__health = 99
        self.__spec = 100
        
    def start_timer(self):
        self.__start_time = time.time()
  
    def set_id(self, id):
        self.__id = id

    def set_money(self, money):
        self.__money = money
  
    def set_wins(self, wins):
        self.__wins = wins
  
    def set_losses(self, losses):
        self.__losses = losses
  
    def set_items(self, items):
        self.__items = items

    def add_item(self, item):
        self.__items.append(item)

    def get_id(self):
        return self.__id

    def get_money(self):
        return self.__money
  
    def get_wins(self):
        return self.__wins
  
    def get_losses(self):
        return self.__losses

    def get_items(self):
        return self.__items

    def get_wait_time(self):
        if self.__start_time == None:
            return None

        return time.time() - self.__start_time
    
    def get_spec(self):
        return self.__spec
    
    def get_discord_display_name(self):
        return self.__discord_display_name
    
    def get_discord_user(self):
        return self.__discord_user
    
    def get_health(self):
        return self.__health
    
    def get_health_bar(self):
        depleted_health_block = '░'
        remaining_health_block = '█'

        health_blocks = m.ceil(self.__health / 10.0)

        return remaining_health_block * health_blocks + depleted_health_block * (10 - health_blocks)
    
    def get_spec_bar(self):
        depleted_spec_block = '░'
        remaining_spec_block = '█'

        spec_blocks = m.ceil(self.__spec / 10.0)

        return remaining_spec_block * spec_blocks + depleted_spec_block * (10 - spec_blocks)
    
    def set_health(self, health):
        self.__health = health
    
    def decrease_health(self, hit):
        self.__health = self.__health - hit
        if self.__health < 0:
            self.__health = 0
    
    def decrease_spec(self, spec_used):
        self.__spec = self.__spec - spec_used
        
def setup(client):
    client.add_cog(Player(None, None))