from discord.ext import commands
import discord

help_pages = {
    1:
        {'page_title' : 'Introduction',
         'description': 'description',
         'example_use': 'placeholder',
         'cmd_aliases': 'placeholder'},
    2:
        {'page_title' : 'Deathmatch',
         'description': 'description',
         'example_use': 'placeholder',
         'cmd_aliases': 'placeholder'},
    3:
        {'page_title' : 'Dice Duel',
         'description': 'description',
         'example_use': 'placeholder',
         'cmd_aliases': 'placeholder'},
    4:
        {'page_title' : 'Profile',
         'description': 'description',
         'example_use': 'placeholder',
         'cmd_aliases': 'placeholder'},
    5:
        {'page_title' : 'Store',
         'description': 'description',
         'example_use': 'placeholder',
         'cmd_aliases': 'placeholder'}
    }

def page_embed(page_number):
    page = help_pages[page_number+1]
    embed = discord.Embed(title=page['page_title'], description=page['description'], colour=discord.Colour.teal())
    embed.set_thumbnail(url="https://i.imgur.com/BfueYr9.png")
    embed.add_field(name='Example Usage:', value=page['example_use'], inline=True)
    embed.add_field(name='Aliases:', value=page['cmd_aliases'], inline=True)
    return embed


class Help(commands.Cog):
    """Lists all cogs and commands"""

    def __init__(self, client):
        self.client = client

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(pass_context=True)
    async def help(self, context):
        message = await context.send(embed=page_embed(0))

        await message.add_reaction('⏮')
        await message.add_reaction('◀')
        await message.add_reaction('▶')
        await message.add_reaction('⏭')

        i, emoji = [0, '']

        while True:
            if emoji == '⏮':
                i = 0
                await message.edit(embed=page_embed(i))
            if emoji == '◀':
                if i > 0:
                    i -= 1
                    await message.edit(embed=page_embed(i))
            if emoji == '▶':
                if i < (len(help_pages) - 1):
                    i += 1
                    await message.edit(embed=page_embed(i))
            if emoji == '⏭':
                i = (len(help_pages) - 1)
                await message.edit(embed=page_embed(i))

            response = await self.client.wait_for('reaction_add', timeout=30)
            if response is None:
                break
            if str(response[1]) != 'iDM#7035' and str(response[1]) != context.message.author.id:   # So bot doesn't trigger from it's own reactions
                emoji = str(response[0].emoji)
                await message.remove_reaction(response[0].emoji, response[1])

        await context.clear_reactions(message)

def setup(client):
    client.add_cog(Help(client))