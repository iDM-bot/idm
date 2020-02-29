from discord.ext import commands
from dm.waiting_room import WaitingRoom
from dm.player import get_player, players_table
import asyncio
import random
import json

IDM_HIT_TIMEOUT = 45

class DeathMatch(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.waiting_rooms = {}
        self.is_dm_executing = {}

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
    async def death_match(self, context, *wager):
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

        amount = None

        if wager:
            amount = wager[0]

        int_amount = self.convert_value(amount)

        if int_amount is None:
            return await context.send(f'{context.message.author.name} your wager was invalid!')

        player = get_player(user, user_id, display_name)
                    
        if int(player.get_money()) < max(int_amount, channel_waiting_room.get_wager_amount()):
            return await context.send(
                f'{context.message.author.name}, you do not have enough gp to cover the wager!')

        if channel_waiting_room.get_wager_amount() is -1:
            channel_waiting_room.set_wager_amount(int_amount)
            channel_waiting_room.str_amount = amount

        try:
            # Queue the person.
            if not channel_waiting_room.is_player_waiting(user_id) and not self.is_dm_executing[channel_id]:
                await context.send(
                    f'**{display_name}** [Wins: **{player.get_wins()}** | Losses: **{player.get_losses()}**] has requested a Death Match{channel_waiting_room.get_purse()[1]}!'
                )
                    
                channel_waiting_room.add_player_to_queue(player)

            if channel_waiting_room.count_players_waiting() >= 2:
                player1 = await channel_waiting_room.get_player_from_queue()
                player2 = await channel_waiting_room.get_player_from_queue()

                if int(player2.get_money()) < int_amount:
                    return await context.send(
                        f'{context.message.author.name}, you do not have enough gp to cover the wager!')

                if not (channel_id in self.is_dm_executing) or not self.is_dm_executing[channel_id]:
                    self.is_dm_executing[channel_id] = True
                    dm = asyncio.get_event_loop()
                    dm.create_task(self.execute_dm(channel_id, context, player1, player2, channel_waiting_room.get_wager_amount(), channel_waiting_room.get_purse()))
                    
        except Exception as err:
            return print(err)
        
        return
            
    async def execute_dm(self, channel_id, context, player1, player2, int_amount, purse):

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

        await context.send(
            f'''**{winner.get_discord_display_name()}** `won` the death match! Sorry, **{loser.get_discord_display_name()}** you lost!'''
        )

        winner_reward = self.roll_gp_drop() * 10**6
        loser_reward = self.roll_gp_drop() * 10**5

        # Reward winner
        await context.send(
            f'**{winner.get_discord_display_name()}** you `won` **{self.convert_number_to_string(int(winner_reward) + int(int_amount))} gp**!'
        )

        # Reward loser
        if timeout_player1 is None and timeout_player2 is None:
            loser_reward = 0
        
        loser_total = -1 * int_amount + loser_reward
        
        won_or_lost = 'won' if loser_total >= 0 else 'lost'

        await context.send(
            f'**{loser.get_discord_display_name()}** you `{won_or_lost}` **{self.convert_number_to_string(-1 * int(int_amount) + int(loser_reward))} gp**!'
        )
            
        loser.set_losses(loser.get_losses() + 1)
        loser.add_money(-1 * int(int_amount) + int(loser_reward))

        winner.set_wins(winner.get_wins() + 1)
        winner.add_money(int(int_amount) + int(winner_reward))

        self.write_player_money(winner)
        self.write_player_money(loser)

        self.waiting_rooms[channel_id].set_wager_amount(-1)
        
        self.is_dm_executing[channel_id] = False

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

        return await self.attack_message(attack_player, other_player, hit_string, weapon, context)

    def calculate_spec(self, weapon):
        hits = [random.randint(0, weapon["spec_max"]) for _ in range(0, weapon["spec_hit"])]

        return sum(hits), '-'.join([f'**{hit}**' for hit in hits])

    def is_float(self, num):
        try:
            float(num)
        except:
            return False

        return True

    def convert_value(self, value: str):
        if value is None:
            return 0

        multipliers = {'k': 10 ** 3, 'm': 10 ** 6, 'b': 10 ** 9, 't': 10 ** 12}

        if value[-1] in multipliers:
            if self.is_float(value[:-1]):
                converted_value = int(float(value[:-1]) * multipliers[value[-1]])

                return converted_value if converted_value > 0 else None
            else:
                return None

        if value.isnumeric():
            return int(value) if int(value) >= 0 else None

        else:
            return None

    def write_player_money(self, player):
        players_table.update({"_id": player.get_id()}, {
            "$set": {"money": str(player.get_money()),
                     "losses": player.get_losses(),
                     "wins": player.get_wins()}})
    
    def convert_number_to_string(self, number: int):
        multiplier_strings = {'k': 3, 'm': 6, 'b': 9, 't': 12}

        if number < 0:
            number = abs(number)
        exponent = 0
        while number > 0:
            if number < 10:
                break
            
            exponent += 1
            number /= 10
        
        prev_multiplier = 0
        prev_abbrev = ''

        for abbrev, multiplier in multiplier_strings.items():
            if exponent > prev_multiplier and exponent < multiplier:
                number = number * 10 ** (exponent - prev_multiplier)
                if number / int(number) > 1:
                    return f'{number:.1f}{prev_abbrev}'

                return f'{int(number)}{prev_abbrev}'

            elif exponent == multiplier:
                return f'{int(number)}{abbrev}'
            
            prev_multiplier = multiplier
            prev_abbrev = abbrev

        return f'0'

    def roll_gp_drop(self):
        gp_tier = {
            1: range(0, 800),
            5: range(800, 1200),
            10: range(1200, 1240),
            50: range(1240, 1248),
            150: range(1248, 1250)
        }
        
        roll = random.randint(0, 1250)
        
        for gp_award, table_range in gp_tier.items():
            if roll in table_range:
                return gp_award

        return 0


def setup(client):
    client.add_cog(DeathMatch(client))
