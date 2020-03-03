from discord.ext.commands import has_permissions
from config import db_connection_string
from discord.ext import commands
from pymongo import MongoClient
import config
import time
import os

mongo_client = MongoClient(db_connection_string)
servers_table = mongo_client.idm.servers


def get_prefix(client, context):
    result = servers_table.find_one({"_id": context.guild.id})
    return result['prefix']

client = commands.Bot(command_prefix = get_prefix, description = config.bot_description)
client.remove_command('help')

@client.event
async def on_ready():
    print('-'*34)
    print('Logged in as: ', client.user.name)
    print('Client ID:    ', client.user.id)
    print('Local time:   ', config.server_time)
    print('-'*34)

@client.event
async def on_guild_join(guild):
    result = servers_table.find_one({"_id": guild.id})
    if result:
        return
    server = {'_id': guild.id, 'name': guild.name, 'prefix': '!'}
    servers_table.insert_one(server)

    # TODO: Create server join message

@client.event
async def on_guild_remove(guild):
    result = servers_table.find_one({"_id": guild.id})
    servers_table.delete_one(result)

@client.command(hidden=True, pass_context=True)
async def ping(context):
    before = time.monotonic()
    message = await context.channel.send("Pong!")
    server_ping = f'Ping: {int((time.monotonic() - before) * 1000)}ms'
    await message.edit(content=server_ping)

@client.command(aliases=['idm_prefix'])
@has_permissions(administrator=True)
async def change_prefix(context, new_prefix):
    # Custom prefixes on a per-server basis in order to prevent different bots from overlapping
    # TODO: Make this an admin only command
    # TODO: Change prefix quantifier (right word?) to utilize RegEx for non-alphanumeric keyboard characters
    #       idk how to regex [./<>?;:"'`!@#$%^&*()\[\]{}_+=|\\-]
    if len(new_prefix) == 1:
        result = servers_table.find_one({"_id": context.channel.guild.id})
        if result:
            servers_table.update_one({'_id': result['_id']}, {'$set': {'prefix': new_prefix}})
            await context.send(f'Prefix changed to: `{new_prefix}`')
        else:
            await context.send(f'Database error')
    else:
        await context.send(f'`{new_prefix}` is not a valid prefix')

@client.event
async def on_message(context):
    message = str(context.content.lower())
    if context.author == client.user:
        return
    if message.find('nobody will ever say this') != -1:
        await context.channel.send(f'That\'s where you\'re wrong, {context.author.mention}')
    await client.process_commands(context)

def load_extensions():
    dir_list = ['dice', 'dm', 'general']
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