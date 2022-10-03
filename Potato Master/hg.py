import asyncio
import typing
import discord
from discord import app_commands
from discord.ext import commands
from numpy import random as npr
from Mongo.MongoHG import MongoHG
from HGMessages.default import default_alive, default_dead, default_barely_survived


# Hunger Games Module
class HG(commands.GroupCog, name='hg', description='The main subcommand of hunger games.'):
    def __init__(self, bot):
        self.bot = bot

    """

        THIS IS A SUBGROUP, MEANT FOR EVERYTHING RELATING TO MESSAGES!
        At the moment includes:
            /hg message list [type]
            /hg message add [type] [message]
            /hg message remove [type] [id]

    """
    messages_group = app_commands.Group(name='message', description='The messages subgroup of hg.', guild_only=True)

    @messages_group.command(name='list', description='Show a list of all the messages.')
    @app_commands.rename(message_type='type')
    @app_commands.describe(message_type='Pick a type of message to show a list of.')
    async def message_list(self, interaction: discord.Interaction, message_type: typing.Literal['alive', 'dead']):
        """
            A list of all the messages, but only one type can be shown at the time.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)

        # Generally important variables
        embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title='Message List')
        the_message = []
        temp_str = ''

        # Code
        if message_type == 'alive':
            if mongo.msg(msg_type='alive').count_documents({}) > 0:
                for msg in mongo.msg(msg_type='alive').find().sort("_id", 1):
                    the_message.append(msg)
                for final_message in the_message:
                    temp_str += f'[{final_message["_id"]}] {final_message["message"]}\n'
                fields = len(the_message) / 8
                if fields > 1:
                    while fields > 0:
                        temp_str = ''
                        another_temp_list = []
                        for final_message in the_message:
                            another_temp_list.append([final_message["_id"], final_message["message"]])
                        for added_message in range(8):
                            if len(another_temp_list) < 1:
                                break
                            else:
                                temp_str += f'[{another_temp_list[0][0]}] {another_temp_list[0][1]}\n'
                                another_temp_list.pop(0)
                                the_message.pop(0)
                        embed = embed.add_field(name='[ID] Message', value=temp_str)
                        fields -= 1
                else:
                    embed = embed.add_field(name='[ID] Message', value=temp_str)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message('The list is empty!')
        elif message_type == 'dead':
            if mongo.msg(msg_type='dead').count_documents({}) > 0:
                for msg in mongo.msg(msg_type='dead').find().sort("_id", 1):
                    the_message.append(msg)
                for final_message in the_message:
                    temp_str += f'[{final_message["_id"]}] {final_message["message"]}\n'
                fields = len(the_message) / 8
                if fields > 1:
                    while fields > 0:
                        temp_str = ''
                        another_temp_list = []
                        for final_message in the_message:
                            another_temp_list.append([final_message["_id"], final_message["message"]])
                        for added_message in range(8):
                            if len(another_temp_list) < 1:
                                break
                            else:
                                temp_str += f'[{another_temp_list[0][0]}] {another_temp_list[0][1]}\n'
                                another_temp_list.pop(0)
                                the_message.pop(0)
                        embed = embed.add_field(name='[ID] Message', value=temp_str)
                        fields -= 1
                else:
                    embed = embed.add_field(name='[ID] Message', value=temp_str)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message('The list is empty!')

    @messages_group.command(name='add', description='Add a custom message for dying or living.')
    @app_commands.rename(message_type='type')
    @app_commands.describe(message_type='Type of message to add.',
                           message='Limit is 96 characters, including symbols and spaces')
    async def message_add(self, interaction: discord.Interaction, message_type: typing.Literal['alive', 'dead'],
                          message: str):
        """
            Add a new message to the database, could be either a message for dying playing, or living player.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)
        # Generally important variables
        message_id = 0
        find_message_id = []

        # Code
        if not len(message) > 96:
            if message_type == 'alive':
                if mongo.msg(msg_type='alive').count_documents({}) <= 100:
                    while message_id <= 1000:
                        look_for = mongo.msg(msg_type='alive').find({"_id": message_id})
                        for found_or_not in look_for:
                            find_message_id.append(found_or_not)
                        if len(find_message_id) < 1:
                            mongo.msg(msg_type='alive').insert_one({"_id": message_id, "message": f"{message}"})
                            await interaction.response.send_message(f'Added custom message to alive list with ID {message_id}.')
                            return
                        else:
                            message_id += 1
                            find_message_id.clear()
                else:
                    await interaction.response.send_message('Message limit for alive reached!')
            elif message_type == 'dead':
                if mongo.msg(msg_type='dead').count_documents({}) <= 96:
                    while message_id <= 1000:
                        look_for = mongo.msg(msg_type='dead').find({"_id": message_id})
                        for found in look_for:
                            find_message_id.append(found)
                        if len(find_message_id) < 1:
                            mongo.msg(msg_type='dead').insert_one({"_id": message_id, "message": f"{message}"})
                            await interaction.response.send_message(
                                f'Added custom message to dead list with ID {message_id}.')
                            return
                        else:
                            message_id += 1
                            find_message_id.clear()
                else:
                    await interaction.response.send_message('Message limit for dead reached!')
        else:
            await interaction.response.send_message('Message too long!', ephemeral=True)

    @messages_group.command(name='remove',
                            description='Remove a custom message, use the list command to learn a message\'s ID.')
    @app_commands.rename(message_id='id', message_type='type')
    @app_commands.describe(message_id='ID of the message being removed.', message_type='Type of message to remove/')
    async def message_remove(self, interaction: discord.Interaction,
                             message_type: typing.Literal['alive', 'dead'], message_id: int):
        """
            Remove a message from the database, ID MUST BE USED! You cannot use the message itself to remove it.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)
        # Generally important variables
        deleted_message = []

        # Code
        if message_type == 'alive':
            if mongo.msg(msg_type='alive').find_one({"_id": message_id}):
                for message in mongo.msg(msg_type='alive').find({"_id": message_id}):
                    deleted_message.append(message)
                mongo.msg(msg_type='alive').delete_one({"_id": message_id})
                for message in deleted_message:
                    await interaction.response.send_message(f'Message "{message["message"]}" has been deleted!')
            elif not mongo.msg(msg_type='alive').find_one({"_id": message_id}):
                await interaction.response.send_message('Message does not exist!')
        elif message_type == 'dead':
            if mongo.msg(msg_type='dead').find_one({"_id": message_id}):
                for message in mongo.msg(msg_type='dead').find({"_id": message_id}):
                    deleted_message.append(message)
                mongo.msg(msg_type='dead').delete_one({"_id": message_id})
                for message in deleted_message:
                    await interaction.response.send_message(f'Message "{message["message"]}" has been deleted!')
            elif not mongo.msg(msg_type='dead').find_one({"_id": message_id}):
                await interaction.response.send_message('Message does not exist!')

    """

        THIS IS A SUBGROUP, MEANT FOR EVERYTHING RELATING TO CONFIGURATIONS! (This usually relates to the database)
        At the moment includes:
            /hg config repair
            /hg config only_custom_messages

    """
    configs_group = app_commands.Group(name='config', description='The config subgroup of hg.', guild_only=True,
                                       default_permissions=discord.Permissions.administrator)

    @configs_group.command(name='repair', description='Repairs all configurations.')
    async def config_repair(self, interaction: discord.Interaction):
        """
            Sets all major configurations to the default values. Should not affect any player made configs.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)

        # Code
        if not mongo.configs().find_one({"_id": 0}):
            mongo.configs().insert_one({"_id": 0, "guild": f"{interaction.guild.name}"})
        mongo.configs().update_one({"running": {"$type": "bool"}},
                                   {"$set": {"_id": 1, "running": False}}, upsert=True)
        mongo.configs().update_one({"stopping": {"$type": "bool"}},
                                   {"$set": {"_id": 2, "stopping": False}}, upsert=True)
        mongo.configs().update_one({"force_stopping": {"$type": "bool"}},
                                   {"$set": {"_id": 3, "force_stopping": False}}, upsert=True)
        mongo.configs().update_one({"only_custom_messages": {"$type": "bool"}},
                                   {"$set": {"_id": 4, "only_custom_messages": False}}, upsert=True)
        await interaction.response.send_message('Configs repaired.')

    @configs_group.command(name='only_custom_messages', description='Toggle only custom messages shown in game.')
    async def config(self, interaction: discord.Interaction):
        """
            Toggles whether only custom messages are shown or not. When True if there are any custom messages in the
            database, only those will be displayed when a game starts. If for some reason the database for alive messages
            or dead messages is empty, the default messages will be used for that type of message. This is implemented
            in the main command.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)

        # Code
        for true_or_false in [mongo.configs().find_one({"_id": 4})]:
            if true_or_false["only_custom_messages"]:
                mongo.configs().update_one({"only_custom_messages": True},
                                           {"$set": {"only_custom_messages": False}})
                await interaction.response.send_message("Only custom messages disabled!")
            else:
                mongo.configs().update_one({"only_custom_messages": False},
                                           {"$set": {"only_custom_messages": True}})
                await interaction.response.send_message("Only custom messages enabled!")

    """

        THIS IS A SUBGROUP, MEANT FOR EVERYTHING RELATING TO ADDING OR REMOVING PLAYERS TO THE DATABASE!
        At the moment includes:
            /hg participants include [user]
            /hg participants include_all
            /hg participants exclude [user]
            /hg participants exclude_all
        
    """
    participants_group = app_commands.Group(name='participants', description='The participants subgroup of hg.',
                                            guild_only=True)

    @participants_group.command(name='include', description='Adds a user to the list of participants.')
    @app_commands.describe(user='Mention the user you wish to add. (Does not actually mention them)')
    async def participants_include(self, interaction: discord.Interaction, user: discord.Member):
        """
            Adds a single user to the database containing all the participants that can currently take part in the game.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)

        # Generally important variables
        not_included = []

        # Code
        check = mongo.participants().find({"_id": user.id})
        for not_inc in check:
            not_included.append(not_inc)
        if not not_included:
            add_user = {"_id": int(user.id),
                        "name": f"{user.display_name}",
                        "mention": f"{user.mention}",
                        "avatar": f"{user.display_avatar}"
                        }
            mongo.participants().insert_one(add_user)
            await interaction.response.send_message(f'Added {user.display_name} to the list of participants!')
        else:
            already_included = await interaction.response.send_message('User has already been included!')
            return already_included

    @participants_group.command(name='include_all', description='Add ALL users on the guild to the list of participants.')
    async def participants_include_all(self, interaction: discord.Interaction):
        """
            Adds ALL users in the guild to the list of participants that can currently take part in the game.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)

        # Generally important variables
        added_number = 0

        # Code
        mongo.participants().delete_many({})
        for user in interaction.guild.members:
            add_user = {"_id": int(user.id),
                        "name": f"{user.display_name}",
                        "mention": f"{user.mention}",
                        "avatar": f"{user.display_avatar}"
                        }
            mongo.participants().insert_one(add_user)
            added_number += 1
        await interaction.response.send_message(f'{added_number} users added to the list of participants.')

    @participants_group.command(name='exclude', description='Exclude a user from the list of participants.')
    @app_commands.describe(user='Mention the user you wish to remove. (Does not actually mention them)')
    async def participants_exclude(self, interaction: discord.Interaction, user: discord.Member):
        """
            Removes a single user from the database containing all the participants.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)

        # Generally important variables
        included = []

        # Code
        check = mongo.participants().find({"_id": user.id})
        for inc in check:
            included.append(inc)
        if included:
            mongo.participants().delete_one({"_id": user.id})
            await interaction.response.send_message(f'{user.display_name} excluded.')
        else:
            await interaction.response.send_message('User is not in the participant list!')

    @participants_group.command(name='exclude_all', description='Exclude ALL users from the list of participants.')
    async def participants_exclude_all(self, interaction: discord.Interaction):
        """
            Removes ALL users from the database containing all the participants.
        """
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)

        # Code
        clear_list = mongo.participants().delete_many({})
        await interaction.response.send_message(f'{clear_list.deleted_count} users excluded.')

    """

        THIS IS THE REST OF THE COMMANDS, PART OF THE MAIN GROUP!
        At the moment includes:
            /hg start
            /hg stop

    """

    # TO-DO: ADD MORE DOCUMENTATION/COMMENTS, it will be hard to read otherwise soon enough
    # MORE TO-DO: Improve the code in general
    # EVEN MORE TO-DO: (not any time soon) Scoreboard and custom NPCs (for the loners out there).
    # NOT THE FINAL VERSION, this is more to see if I could, and in the future I will make a better
    # more feature rich one (probably, if I am not lazy)
    @app_commands.command(name='start', description='Start the hunger games!')
    @commands.guild_only()
    async def hunger_games(self, interaction: discord.Interaction):
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)

        # Generally important variables
        day = 1
        dead = []
        temp_day_dead = []

        # Adding all messages to one usable variable
        dead_msg = [db_message["message"] for db_message in list(mongo.msg(msg_type='dead').find())]
        alive_msg = [db_message["message"] for db_message in list(mongo.msg(msg_type='alive').find())]

        # Finds out where the use default messages or not (stored in HGMessages/default.py as variables)
        for only_custom in [mongo.configs().find_one({"_id": 4})]:
            if not only_custom["only_custom_messages"]:
                dead_msg = [message for message in default_dead]
                alive_msg = [message for message in default_alive]
            elif only_custom["only_custom_messages"]:
                check_dead = list(mongo.msg(msg_type='dead').find())
                check_alive = list(mongo.msg(msg_type='alive').find())
                if len(check_dead) >= 1 <= len(check_alive):
                    break
                elif len(check_dead) < 1 <= len(check_alive):
                    await interaction.channel.send("No custom dead messages found, so using default.")
                    dead_msg = [message for message in default_dead]
                elif len(check_dead) >= 1 > len(check_alive):
                    await interaction.channel.send("No custom alive messages found, so using default.")
                    alive_msg = [message for message in default_alive]
                elif len(check_dead) < 1 > len(check_alive):
                    await interaction.channel.send("No custom messages found, so using defaults.")
                    dead_msg = [message for message in default_dead]
                    alive_msg = [message for message in default_alive]
        barely_survived_msg = [message for message in default_barely_survived]

        # CHECK IF THERE IS AT LEAST 2 PLAYERS
        participant_count = mongo.participants().count_documents({}, limit=2)
        if participant_count > 1:
            # Check if a game is already running
            currently_running = [mongo.configs().find_one({"_id": 1})]
            if not currently_running[0]["running"]:
                # The initial list of participants (users)
                temp = ''
                participant_list = mongo.participants().find()
                alive = [user for user in participant_list]
                await interaction.response.send_message('Game starting with the following users!')
                for user in alive:
                    temp += f'{user["name"]}\n'
                embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title='Participants')
                await interaction.channel.send(embed=embed.add_field(name=f'1-{len(alive)}', value=temp))
                # THE ACTUAL GAME
                while len(alive) > 1:
                    # Set hunger games to RUNNING
                    running_current = {"running": False}
                    running_new = {"$set": {"running": True}}
                    mongo.configs().update_one(running_current, running_new)
                    npr.shuffle(alive)
                    await asyncio.sleep(2)
                    await interaction.followup.send(f'Day {day} incoming!')
                    await asyncio.sleep(4)
                    alive_count = len(alive)
                    # This determines the outcome for each player that is ALIVE
                    for participant in alive:
                        # Shuffles the messages and determines outcome
                        outcome = npr.choice(["alive", "dead", "barely alive", 0], p=[0.55, 0.445, 0.005, 0.0])

                        # Living outcome
                        if outcome == 'alive':
                            embed = discord.Embed(colour=discord.Colour.green(), description=f'{npr.choice(alive_msg)}')
                            await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                  icon_url=f'{participant["avatar"]}'))

                        # Dying outcome
                        elif outcome == 'dead':
                            if alive_count > 1:
                                embed = discord.Embed(colour=discord.Colour.from_rgb(135, 0, 0),
                                                      description=f'{npr.choice(dead_msg)}')
                                await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                      icon_url=f'{participant["avatar"]}'))
                                temp_day_dead.append(participant)
                                participant.update({"name": f'~~{participant["name"]}~~'})
                                dead.append(participant)
                                alive_count -= 1
                            else:
                                embed = discord.Embed(colour=discord.Colour.yellow(),
                                                      description=f'***Barely scraped by!***')
                                await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                      icon_url=f'{participant["avatar"]}'))

                        # A very lucky participant!
                        else:
                            embed = discord.Embed(colour=discord.Colour.yellow(),
                                                  description=f'{npr.choice(barely_survived_msg)}')
                            await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                  icon_url=f'{participant["avatar"]}'))
                        await asyncio.sleep(2)
                    await asyncio.sleep(2)
                    for dead_participant in temp_day_dead:
                        alive.remove(dead_participant)
                    else:
                        temp_day_dead.clear()
                    if len(alive) > 1:
                        temp_la = ''
                        temp_ld = ''
                        for participant in alive:
                            temp_la += f'{participant["name"]}\n'
                        for participant in dead:
                            temp_ld += f'*{participant["name"]}*\n'
                        alive_dead = temp_la + temp_ld
                        total = len(alive) + len(dead)
                        embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title=f'Day {day} Summary')
                        await interaction.channel.send(embed=embed.add_field(name=f'1-{total}', value=alive_dead))
                        day += 1
                    # Check if the game is supposed to stop now
                    stopping = [mongo.configs().find_one({"_id": 2})]
                    if stopping[0]["stopping"]:
                        break
                stopping = [mongo.configs().find_one({"_id": 2})]
                if stopping[0]["stopping"]:
                    mongo.configs().update_one({"running": True}, {"$set": {"running": False}})
                    mongo.configs().update_one({"stopping": True}, {"$set": {"stopping": False}})
                    await interaction.followup.send('Game stopping!')
                    return
                else:
                    mongo.configs().update_one({"running": True}, {"$set": {"running": False}})
                    winner = alive[0]
                    await interaction.channel.send(f'{winner["name"]} is the winner of this bout!')
            elif currently_running[0]["running"]:
                await interaction.response.send_message('A game is currently running!')
        else:
            await interaction.response.send_message('Please include at least 2 players!')

    @app_commands.command(name='stop', description='Stop the current game at the end of the current day.')
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def hunger_games_stop(self, interaction: discord.Interaction):
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)
        # Code
        stopping = [mongo.configs().find_one({"_id": 2})]
        running = [mongo.configs().find_one({"_id": 1})]
        if not stopping[0]["stopping"] and running[0]["running"]:
            stopping_current = {"stopping": False}
            stopping_new = {"$set": {"stopping": True}}
            mongo.configs().update_one(stopping_current, stopping_new)
            await interaction.response.send_message('Game ending at the end of the current day!')
        elif not stopping[0]["stopping"] and not running[0]["running"]:
            await interaction.response.send_message('No game is currently running!')
        elif stopping[0]["stopping"]:
            await interaction.response.send_message('Game already stopping!')


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(HG(bot))
