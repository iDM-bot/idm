from config import db_connection_string
from pymongo import MongoClient
import math as m
import discord
import time

mongo_client = MongoClient(db_connection_string)
players_table = mongo_client.idm.players

def get_player(discord_user, user_id, display_name):
    result = players_table.find_one({"_id": user_id})

    if result is None:
        default_player = {
            '_id': user_id,
            'wins': 0,
            'losses': 0,
            'money': '0',
            'items': ['dds', 'whip'],
            'dice_wins': 0,
            'dice_losses': 0
        }

        players_table.insert_one(default_player)

        result = default_player

    player = Player(discord_user, display_name)

    player.set_id(user_id)
    player.set_items(set(result['items']))
    player.set_losses(result['losses'])
    player.set_money(result['money'])
    player.set_wins(result['wins'])
    player.set_dice_wins(result['dice_wins'])
    player.set_dice_losses(result['dice_losses'])

    return player

class Player:

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
        self.__dice_losses = 0
        self.__dice_wins = 0
        
    def start_timer(self):
        self.__start_time = time.time()
  
    def set_id(self, id):
        self.__id = id

    def set_money(self, money):
        self.__money = money
  
    def set_wins(self, wins):
        self.__wins = wins
    
    def get_dice_wins(self):
        return self.__dice_wins
    
    def get_dice_losses(self):
        return self.__dice_losses
    
    def set_dice_wins(self, wins):
        if wins is None:
            wins = 0
        self.__dice_wins = int(wins)
    
    def set_dice_losses(self, losses):
        if losses is None:
            losses = 0
        self.__dice_losses = int(losses)
  
    def set_losses(self, losses):
        self.__losses = losses
  
    def set_items(self, items):
        self.__items = items

    def add_item(self, item):
        self.__items.append(item)
    
    def add_money(self, amount):
        self.__money = int(self.__money) + int(amount)

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
    
    def add_dice_win(self):
        self.__dice_wins = int(self.__dice_wins) + 1
    
    def add_dice_loss(self):
        self.__dice_losses = int(self.__dice_losses) + 1
    
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