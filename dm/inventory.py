from discord.ext import commands
import json

def list_weapons():
    store_list = []
    with open('./dm/weapon.json', 'r') as json_file:
        data = json.load(json_file)
        for p in data:
            store_list.append(p['name'])
        store_output = ", ".join(map(str, store_list))
    return store_output

class Store(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(name="weapons",
                      description="List all weapons",
                      brief="weapons brief",
                      pass_context=True)
    async def weapons(self, context):
        await context.send(list_weapons())


def setup(client):
    client.add_cog(Store(client))