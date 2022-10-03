import typing
import discord
from discord import app_commands
from discord.ext import commands
from Mongo.MongoHG import MongoHG

"""

    This module is solely for the purpose of developing and testing new commands that could potentially mess up the
    bot or could lead to something going wrong with the core functionality of the bot.
    
    Or just if I want to leave some existing command alone while I make a new version of it here.

"""


# Hunger Games MESSAGES module
class Dev(commands.GroupCog, name='dev', description='Commands in development.'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='list', description='[DEV] Show a list of all the messages.')
    async def message_list(self, interaction: discord.Interaction, message_type: typing.Literal['alive', 'dead']):
        """
            === DEV ===
            A list of all the messages, but only one type can be shown at the time.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)
        mongo_msg = mongo.msg(msg_type=message_type)

        def message_embed(page_number) -> int:
            match page_number:
                case 1:
                    return 0
                case 2:
                    return 20
                case 3:
                    return 40
                case 4:
                    return 60
                case 5:
                    return 80

        def embed_test(page_number):
            if mongo_msg.count_documents({}) > 0:
                local_embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title='Message List')
                message_dict_list = []
                msg1 = ''
                msg2 = ''
                for i, msg_dict in enumerate(
                        mongo_msg.find().sort("_id", 1).skip(message_embed(page_number)).limit(20)):
                    message_dict_list.append(msg_dict)
                    if i < 10:
                        msg1 = msg1 + f'[{msg_dict["_id"]}] {msg_dict["message"]}\n'
                    else:
                        msg2 = msg2 + f'[{msg_dict["_id"]}] {msg_dict["message"]}\n'
                if mongo_msg.count_documents({}) / 20 > 1:
                    for count in range(2):
                        if count == 0:
                            local_embed = local_embed.add_field(name='[ID] Message', value=msg1)
                        else:
                            local_embed = local_embed.add_field(name='[ID] Message', value=msg2)
                    else:
                        return local_embed
                else:
                    local_embed = local_embed.add_field(name='[ID] Message', value=msg1)
                    if msg2:
                        local_embed = local_embed.add_field(name='[ID] Message', value=msg2)
                    return local_embed

        class MessageList(discord.ui.View):
            def __init__(self, choice):
                super().__init__()
                self.choice = choice
                self.embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title='Message List')
                self.page = 1

            @discord.ui.button(label='Next', style=discord.ButtonStyle.grey)
            async def next(self, inter: discord.Interaction, button: discord.ui.Button):
                if self.page < 5:
                    self.page += 1
                    embed = embed_test(self.page)
                    await interaction.response.edit_message(embed=embed, view=view)
                else:
                    pass

            @discord.ui.button(label='Last', style=discord.ButtonStyle.grey)
            async def last(self, inter: discord.Interaction, button: discord.ui.Button):
                if self.page > 1:
                    self.page -= 1
                    embed = embed_test(self.page)
                    await interaction.response.edit_message(embed=embed, view=view)
                else:
                    pass

        view = MessageList(choice=message_type)
        embed_page_one = embed_test(1)
        await interaction.response.send_message(embed=embed_page_one, view=view)

        """if mongo_msg.count_documents({}) > 0:
            message_dict_list = []
            msg1 = ''
            msg2 = ''
            for i, msg_dict in enumerate(mongo_msg.find().sort("_id", 1).skip(message_embed(page)).limit(20)):
                message_dict_list.append(msg_dict)
                if i < 10:
                    msg1 = msg1 + f'[{msg_dict["_id"]}] {msg_dict["message"]}\n'
                else:
                    msg2 = msg2 + f'[{msg_dict["_id"]}] {msg_dict["message"]}\n'
            if mongo_msg.count_documents({})/20 > 1:
                for count in range(2):
                    if count == 0:
                        embed = embed.add_field(name='[ID] Message', value=msg1)
                    else:
                        embed = embed.add_field(name='[ID] Message', value=msg2)
                else:
                    await interaction.response.send_message(embed=embed)
            else:
                embed = embed.add_field(name='[ID] Message', value=msg1)
                if msg2:
                    embed = embed.add_field(name='[ID] Message', value=msg2)
                await interaction.response.send_message(embed=embed)"""


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Dev(bot))
