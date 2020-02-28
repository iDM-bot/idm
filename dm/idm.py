from discord.ext import commands 
import discord
from config import db_connection_string, server_time
from pymongo import MongoClient
from dm.waiting_room import WaitingRoom
from dm.player import Player
import asyncio
import random
import json

mongo_client = MongoClient(db_connection_string)
players_table = mongo_client.idm.players

def get_player(discord_user, user_id, display_name):
    result = players_table.find_one({"_id": user_id})

    if not 'dice_wins' in result:
        result['dice_wins'] = 0
        result['dice_losses'] = 0

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

IDM_HIT_TIMEOUT = 45

class DeathMatch(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.waiting_rooms = {}
        self.is_dm_executing = {}
        self.in_dice_duel = set()
        
        self.weapons = {}

        self.weapon_aliases = {}

        with open('./dm/weapon.json', 'r') as weapons_file:
            weapons = json.load(weapons_file)
            self.weapons = {weapons[i]["id"]: weapons[i] for i in range(0, len(weapons))}
            self.weapon_aliases = {weapons[i]["alias"]: weapons[i]["id"] for i in range(0, len(weapons))}
   
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name="dm",
                      description="dm description",
                      brief="dm brief",
                      pass_context=True)
    async def death_match(self, context):
        user = context.message.author
        display_name = context.message.author.display_name
        user_id = context.message.author.id

        channel_id = context.message.channel.id

        if not channel_id in self.waiting_rooms:
            self.waiting_rooms[channel_id] = WaitingRoom(context)
            self.is_dm_executing[channel_id] = False
            loop = asyncio.get_event_loop()
            loop.create_task(self.waiting_rooms[channel_id].run_timeout_routine())

        channel_waiting_room = self.waiting_rooms[channel_id]

        try:
            # Queue the person.
            if not channel_waiting_room.is_player_waiting(user_id) and not self.is_dm_executing[channel_id]:
                player = get_player(user, user_id, display_name)
                
                await context.send(
                    f'**{display_name}** [Wins: **{player.get_wins()}** | Losses: **{player.get_losses()}**] has requested a Death Match!'
                )
                    
                channel_waiting_room.add_player_to_queue(player)

            if channel_waiting_room.count_players_waiting() >= 2:
                player1 = await channel_waiting_room.get_player_from_queue()
                player2 = await channel_waiting_room.get_player_from_queue()

                if not (channel_id in self.is_dm_executing) or not self.is_dm_executing[channel_id]:
                    self.is_dm_executing[channel_id] = True
                    dm = asyncio.get_event_loop()
                    dm.create_task(self.execute_dm(channel_id, context, player1, player2))
                    
        except Exception as err:
            return
        
        return
            
    async def execute_dm(self, channel_id, context, player1, player2):
        result = {}

        self.is_dm_executing[channel_id] = True

        players = [player1, player2]
        first_player = random.randint(0, 1)

        first_hit_player = players[first_player]
        second_hit_player = player2 if first_hit_player is player1 else player1

        await context.send(
            f'**{player1.get_discord_display_name()}** vs **{player2.get_discord_display_name()}**! Let the fight begin! **{players[first_player].get_discord_display_name()}** goes first!'
        )
        
        timeout_player1 = None
        timeout_player2 = None

        while player1.get_health() > 0 and player2.get_health() > 0:
            
            timeout_player1 = await self.attack_player(first_hit_player, second_hit_player, context, channel_id)

            if timeout_player1 is not None:
                await context.send('**DM timed out. Player took too long to respond.**')
                break

            if second_hit_player.get_health() > 0:

                timeout_player2 = await self.attack_player(second_hit_player, first_hit_player, context, channel_id)
            
                if timeout_player2 is not None:
                    await context.send('**DM timed out. Player took too long to respond.**')
                    break
    
        winner = player1
        loser = player2

        if player1.get_health() <= 0:
            winner = player2
            loser = player1

        if timeout_player1 is not None:
            loser = first_hit_player
            winner = second_hit_player

        elif timeout_player2 is not None:
            loser = second_hit_player
            winner = first_hit_player
            
        result['winner'] = winner
        result['loser'] = loser

        winner.set_wins(winner.get_wins() + 1)
        loser.set_losses(loser.get_losses() + 1)
        
        await context.send(
            f'''**{winner.get_discord_display_name()}** won the death match! Sorry, **{loser.get_discord_display_name()}** you lost!'''
        )
        
        self.is_dm_executing[channel_id] = False

        self.write_stats(result)

        return
    
    async def attack_message(self, attack_player, other_player, hit, weapon, context):
        await context.send(
            f'**{attack_player.get_discord_display_name()}** {weapon["action_verb"]} **{other_player.get_discord_display_name()}** for a {hit} with **{weapon["name"]}**'
        )
        
        await context.send(
            f'**{attack_player.get_discord_display_name()}** Spec **{attack_player.get_spec_bar()} {attack_player.get_spec()}%**! **{other_player.get_discord_display_name()}** HP **{other_player.get_health_bar()} {other_player.get_health()}**'
        )

        return

    async def get_player_weapon_choice(self, player, channel_id):
        def valid_input(message):
            tokens = message.content.split(' ')
            weapon_key = (tokens[0]).lower()

            if player.get_discord_user() == message.author and weapon_key in self.weapon_aliases and channel_id == message.channel.id:
                if len(tokens) == 2 and tokens[1] == 'spec':
                    weapon = self.weapons[self.weapon_aliases[weapon_key]]
                    if player.get_spec() < weapon["spec_use"]:
                        return False

                return True
            
            return False
        
        try:
            tokens = (await asyncio.wait_for(self.client.wait_for('message', check=valid_input), timeout=IDM_HIT_TIMEOUT)).content.split(" ")

            weapon = tokens[0].lower()
            spec = False

            if len(tokens) == 2:
                spec = tokens[1].lower() == 'spec'
            
            return self.weapons[self.weapon_aliases[weapon]], spec, None

        except asyncio.TimeoutError:
            return None, None, player

    
    def compute_hit(self, attack_player, other_player, weapon, spec):
        max_hit = weapon["max_hit"]

        hit = random.randint(0, max_hit)
        
        hit_string = f'**{hit}**'
        if spec:
            hit, hit_string = self.calculate_spec(weapon)
            attack_player.decrease_spec(weapon["spec_use"])

        if hit > other_player.get_health():
            hit = other_player.get_health()
        
        other_player.decrease_health(hit)

        return hit_string


    async def attack_player(self, attack_player, other_player, context, channel_id):
        weapon, spec, player = await self.get_player_weapon_choice(attack_player, channel_id)

        if weapon is None:
            return player

        hit_string = self.compute_hit(attack_player, other_player, weapon, spec)

        await self.attack_message(attack_player, other_player, hit_string, weapon, context)

        return
        
    def write_stats(self, stats):
        winner = stats['winner']
        players_table.update({"_id": winner.get_id()}, {"$set": {"losses": winner.get_losses(), "wins": winner.get_wins()}})
        
        loser = stats['loser']
        players_table.update({"_id": loser.get_id()}, {"$set":{"losses": loser.get_losses(), "wins": loser.get_wins()}})

        return


    def calculate_spec(self, weapon):
        hits = [random.randint(0, weapon["spec_max"]) for _ in range(0, weapon["spec_hit"])]

        return sum(hits), '-'.join([f'**{hit}**' for hit in hits])

def setup(client):
    client.add_cog(DeathMatch(client))
