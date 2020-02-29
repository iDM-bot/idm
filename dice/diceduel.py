from dm.player import get_player, players_table
from discord.ext import commands
import discord
import asyncio
import random


class DiceDuel(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.in_dice_duel = set()

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name="addmoney",
                      description="add money - admin command",
                      brief="add money to a player for betas",
                      pass_context=True)
    async def add_money(self, context: commands.Context, recipient: discord.Member, amount):
        if not context.message.author.id in [363762044396371970, 150125122408153088]:
            return

        player = get_player(recipient, recipient.id, recipient.display_name)

        int_amount = self.convert_value(amount)

        if int_amount is None:
            return

        player.add_money(int_amount)

        self.write_player_money(player)

        await context.send(f'**{amount} gp** was successfully added to {recipient.mention}.')

    # @commands.cooldown(1, 1, commands.BucketType.user)
    # @commands.command(name="gp",
    #                   description="get your current gp",
    #                   brief="add money to a player for betas",
    #                   pass_context=True)
    # async def gp(self, context: commands.Context):
    #     author = context.message.author
    #     player = get_player(author, author.id, author.display_name)
    #
    #     await context.send(f'{author.mention} you have {int(player.get_money()):,} gp')

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name="dd",
                      description="dice duel",
                      brief="dice duel",
                      pass_context=False)
    async def dice_duel(self, context: commands.Context, opponent: discord.Member, *wager):
        if context.author in self.in_dice_duel:
            return

        challenger_player = get_player(context.message.author, context.message.author.id,
                                       context.message.author.display_name)
        opponent_player = get_player(opponent, opponent.id, opponent.display_name)

        channel_id = context.channel.id

        if opponent == context.message.author:
            return await context.send(f"You can't duel yourself!")

        if wager:
            amount = wager[0]
            purse = [f' **{amount} gp**', f' for **{amount} gp**']
        if not wager:
            amount, purse = ['0', ['', '']]
        int_amount = self.convert_value(amount)

        if int_amount is None:
            return await context.send(f'{context.message.name} your wager was invalid!')

        if int(challenger_player.get_money()) < int_amount:
            return await context.send(f'{context.message.author.name}, you do not have enough gp to cover the wager!')

        await context.send(
            f'**{context.author.name}** [Wins: **{challenger_player.get_dice_wins()}** Losses: **{challenger_player.get_dice_losses()}**] has challenged {opponent.name} to a dice duel{purse[1]}! \nType `accept` to play or `decline` to reject.')

        int_amount = self.convert_value(amount)
        if int(opponent_player.get_money()) < int_amount:
            return await context.send(f'{context.message.author.name}, you do not have enough gp to cover the wager!')

        def valid_input(message):
            if message.author == opponent and message.content.lower() == 'accept' and channel_id == message.channel.id:
                return True


            return False

        try:
            await asyncio.wait_for(self.client.wait_for('message', check=valid_input), timeout=30)


            await context.send(
                f'**{opponent.name}** [Wins: **{opponent_player.get_dice_wins()}** Losses: **{opponent_player.get_dice_losses()}**] accepted your dice duel!')

            winner = None
            loser = None

            challenger = context.message.author

            self.in_dice_duel.add(challenger)
            self.in_dice_duel.add(opponent)

            while winner is None:
                await context.send(f'{challenger.name}, type `roll`! You have 30 seconds to respond.')
                challenger_first_roll, challenger_second_roll, timeout_player = await self.get_dice_roll(challenger,
                                                                                                         channel_id)

                if timeout_player is not None:
                    winner = opponent_player
                    break

                await context.send(
                    f'{challenger.name} you rolled a **{challenger_first_roll}** and **{challenger_second_roll}**!')

                await context.send(f'{opponent.name}, type `roll`! You have 30 seconds to respond.')
                opponent_first_roll, opponent_second_roll, timeout_player = await self.get_dice_roll(opponent,
                                                                                                     channel_id)

                if timeout_player is not None:
                    winner = challenger_player

                await context.send(
                    f'{opponent.name} you rolled a **{opponent_first_roll}** and **{opponent_second_roll}**!')

                if challenger_first_roll + challenger_second_roll < opponent_first_roll + opponent_second_roll:
                    await context.send(f'Congratulations, {opponent.name} you won{purse[0]}!')
                    winner = opponent_player

                elif challenger_first_roll + challenger_second_roll > opponent_first_roll + opponent_second_roll:
                    await context.send(f'Congratulation, {challenger.name} you won{purse[0]}!')
                    winner = challenger_player

                else:
                    await context.send(f'It\'s a tie! Roll again!')

            if winner == challenger:
                loser = opponent_player
            else:
                loser = challenger_player

            winner.add_money(int(int_amount))
            winner.add_dice_win()

            loser.add_money(-1 * int(int_amount))
            loser.add_dice_loss()

            self.write_player_money(winner)
            self.write_player_money(loser)

            self.in_dice_duel.remove(opponent)
            self.in_dice_duel.remove(challenger)

        except asyncio.TimeoutError:
            await context.send(f'{opponent.display_name} did not respond to your dice duel request.')

            self.in_dice_duel.remove(opponent)
            self.in_dice_duel.remove(challenger)

            return

        return

    async def get_dice_roll(self, dicer, channel_id):
        def valid_challenger_dice_roll(message):
            if message.author.id == dicer.id and message.content.lower() == 'roll' and channel_id == message.channel.id:
                return True

            return False

        try:
            await asyncio.wait_for(self.client.wait_for('message', check=valid_challenger_dice_roll), timeout=30)
        except asyncio.TimeoutError:
            return -1, -1, dicer

        return random.randint(1, 6), random.randint(1, 6), None

    def is_float(self, num):
        try:
            float(num)
        except:
            return False

        return True

    def convert_value(self, value: str):
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
                     "dice_wins": player.get_dice_wins(),
                     "dice_losses": player.get_dice_losses()}})


def setup(client):
    client.add_cog(DiceDuel(client))