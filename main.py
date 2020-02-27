from discord.ext import commands
import config
import time
import json
import os

def get_prefix(client, message):
    try:
        with open('./admin/prefixes.json', 'r') as file:
            prefixes = json.load(file)
        return prefixes[str(message.guild.id)]
    except:
        return '.'

client = commands.Bot(command_prefix = get_prefix, description = config.bot_description)
client.remove_command('help')

@client.event
async def on_ready():
    print('-'*34)
    print('Logged in as: ', client.user.name)
    print('Client ID:    ', client.user.id)
    print('Local time:   ', config.server_time)
    print('-'*34)

@client.command(hidden=True, pass_context=True)
async def ping(context):
    before = time.monotonic()
    message = await context.channel.send("Pong!")
    server_ping = f'Ping: {int((time.monotonic() - before) * 1000)}ms'
    await message.edit(content=server_ping)
    
@client.event
async def on_message(context):
    message = str(context.content.lower())
    if context.author == client.user:
        return
    if message.find('nobody will ever say this') != -1:
        await context.channel.send(f'That\'s where you\'re wrong, {context.author.mention}')
    await client.process_commands(context)

@client.event
async def on_guild_join(guild):
    # Custom prefixes on a per-server basis in order to prevent command overlap
    with open('./admin/prefixes.json', 'r') as file:
        prefixes = json.load(file)
    prefixes[str(guild.id)] = '.'
    with open('./admin/prefixes.json', 'w') as file:
        json.dump(prefixes, file, indent=4)

    # TODO: Create server join message

@client.event
async def on_guild_remove(guild):
    # Removes the custom prefix from prefixes.json
    with open('./admin/prefixes.json', 'r') as file:
        prefixes = json.load(file)
    prefixes.pop(str(guild.id))
    with open('./admin/prefixes.json', 'w') as file:
        json.dump(prefixes, file, indent=4)

@client.command(alias='idm_prefix')
async def change_prefix(context, prefix):
    # Custom prefixes on a per-server basis in order to prevent command overlap
    # TODO: Make this an admin only command
    # TODO: Change prefix quantifier (right word?) to utilize RegEx for non-alphanumeric keyboard characters
    #       idk how to regex [./<>?;:"'`!@#$%^&*()\[\]{}_+=|\\-]
    if len(prefix) == 1:
        with open('./admin/prefixes.json', 'r') as file:
            prefixes = json.load(file)
        prefixes[str(context.guild.id)] = prefix
        with open('./admin/prefixes.json', 'w') as file:
            json.dump(prefixes, file, indent=4)
        await context.send(f'Prefix changed to: {prefix}')
    else:
        await context.send(f'Entry is not a valid prefix')


def load_extensions():
    dir_list = ['idm', 'admin']
    for dir_ in dir_list:
        for filename in os.listdir(f'./{dir_}'):
            cog = filename[:-3]
            if filename.endswith('.py'):
                try:
                    client.load_extension(f'{dir_}.{cog}')
                    print(f'Loaded extension: {cog}')
                except commands.NoEntryPointError:
                    pass
                except Exception as err:
                    exc = f'{type(err).__name__}: {err}'
                    print(f'Failed to load extension {cog}\n{exc}')

def log_in():
    load_extensions()
    print('Attempting to log in...')
    try:
        client.run(config.discord_token)
    except Exception as error:
        print('Discord: Unsuccessful login. Error: ', error)
        quit()

if __name__ == '__main__':
    log_in()