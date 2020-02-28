from discord.ext import commands
import discord
import os

admins = [150125122408153088, 363762044396371970]
dir_list = ['idm', 'lot']

class GeneralCommands(commands.Cog):
    """Lists all cogs and commands"""

    def __init__(self, client):
        self.client = client

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name='invite', pass_context=True, brief='help command')
    async def invite(self, context):
        embed=discord.Embed(title="Invite iDM to your server", url="https://discordapp.com/api/oauth2/authorize?client_id=617836684511412249&permissions=0&scope=bot", color=0x28aab0)
        embed.set_thumbnail(url="https://i.imgur.com/BfueYr9.png")
        embed.add_field(name="Dueling, dicing, & lottery bot", value="A spiritual successor to the iDM bot for IRC", inline=False)
        await context.send(embed=embed)

    @commands.command(pass_context=True)
    async def reload(self, context, dir_: str):
        """Reload the specified cog"""
        if (context.message.author.id in admins) & (dir_ in dir_list):
            for filename in os.listdir(f'./{dir_}'):
                cog = filename[:-3]
                if filename.endswith('.py'):
                    try:
                        self.client.reload_extension(f'{dir_}.{cog}')
                    except Exception as err:
                        exc = f'{type(err).__name__}: {err}'
                        print(f'Failed to load extension {cog}\n{exc}')
            await context.send(f'Reloaded {dir_}')
        else:
            await context.send('Invalid Entry')

    @commands.command(pass_context=True)
    async def load(self, context, dir_: str):
        """Loads the specified cog"""
        if (context.message.author.id in admins) & (dir_ in dir_list):
            for filename in os.listdir(f'./{dir_}'):
                cog = filename[:-3]
                if filename.endswith('.py'):
                    try:
                        self.client.load_extension(f'{dir_}.{cog}')
                    except Exception as err:
                        exc = f'{type(err).__name__}: {err}'
                        print(f'Failed to load extension {cog}\n{exc}')
            await context.send(f'Loaded {dir_}')
        else:
            await context.send('Invalid Entry')

    @commands.command(pass_context=True)
    async def unload(self, context, dir_: str):
        """Unloads the specified cog"""
        if (context.message.author.id in admins) & (dir_ in dir_list):
            for filename in os.listdir(f'./{dir_}'):
                cog = filename[:-3]
                if filename.endswith('.py'):
                    try:
                        self.client.unload_extension(f'{dir_}.{cog}')
                    except Exception as err:
                        exc = f'{type(err).__name__}: {err}'
                        print(f'Failed to load extension {cog}\n{exc}')
            await context.send(f'Unloaded {dir_}')
        else:
            await context.send('Invalid Entry')


def setup(client):
    client.add_cog(GeneralCommands(client))