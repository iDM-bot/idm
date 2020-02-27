from discord.ext import commands
import discord

class GeneralCommands(commands.Cog):
    """Lists all cogs and commands"""

    def __init__(self, client):
        self.client = client

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name='invite', pass_context=True, brief='help command')
    async def invite(self, context):
        embed=discord.Embed(title="Inivite iDM to your server", url="https://discordapp.com/api/oauth2/authorize?client_id=617836684511412249&permissions=0&scope=bot", color=0x28aab0)
        embed.set_thumbnail(url="https://i.imgur.com/BfueYr9.png")
        embed.add_field(name="Dueling, dicing, & lottery bot", value="A spiritual successor to the iDM bot for IRC", inline=False)
        await context.send(embed=embed)


def setup(client):
    client.add_cog(GeneralCommands(client))