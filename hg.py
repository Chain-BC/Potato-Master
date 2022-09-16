import asyncio
import typing
import discord
import pymongo
from discord import app_commands
from discord.ext import commands
from numpy import random as npr


# Everything mongo *Wink*
class MongoDB:
    def __init__(self, discord_id):
        self.discord_id = discord_id
        self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.guild_database = self.mongo_client[f"storage_{self.discord_id}"]

    def msg_alive(self):
        messages_alive_collection = self.guild_database["messages_alive"]
        return messages_alive_collection

    def msg_dead(self):
        messages_dead_collection = self.guild_database["messages_dead"]
        return messages_dead_collection

    def configs(self):
        configs_collection = self.guild_database["configs"]
        return configs_collection

    def participants(self):
        participant_collection = self.guild_database["participant_list"]
        return participant_collection


# Hunger Games Module
class Hg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name='hg', description='All the subcommands for HG.')

    # Configs for hunger games in general!
    @group.command(name='config', description='Tweak various options on the bot or repair it.')
    @app_commands.describe(option='Pick a value to change in the configurations or repair them.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction, option: typing.Literal['repair', 'only_custom_messages']):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        if option == 'repair':
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
            await interaction.response.send_message('Configs set back to default.')
        elif option == 'only_custom_messages':
            for true_or_false in [mongo.configs().find_one({"_id": 4})]:
                if true_or_false["only_custom_messages"]:
                    mongo.configs().update_one({"only_custom_messages": True},
                                               {"$set": {"only_custom_messages": False}})
                    await interaction.response.send_message("Only custom messages disabled!")
                else:
                    mongo.configs().update_one({"only_custom_messages": False},
                                               {"$set": {"only_custom_messages": True}})
                    await interaction.response.send_message("Only custom messages enabled!")

    # Adds a "participant" to the database
    @group.command(name='include', description='Add a player to the list of participants.')
    @app_commands.describe(player='Mention the player you wish to add. (Does not actually mention them)')
    @app_commands.guild_only()
    async def add_user(self, interaction: discord.Interaction, player: discord.Member):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        # Generally important variables
        not_included = []

        # Code
        query = {"_id": player.id}
        check = mongo.participants().find(query)
        for not_inc in check:
            not_included.append(not_inc)
        if not not_included:
            add_player = {"_id": int(player.id),
                          "name": f"{player.display_name}",
                          "mention": f"{player.mention}",
                          "avatar": f"{player.display_avatar}"
                          }
            mongo.participants().insert_one(add_player)
            await interaction.response.send_message(f'Added {player.display_name} to participants!')
        else:
            already_included = await interaction.response.send_message('Player has already been included!')
            return already_included

    # Adds all current guild members to the database
    @group.command(name='include_all', description='Add ALL players on the guild to the list of participants.')
    @app_commands.guild_only()
    async def add_all_users(self, interaction: discord.Interaction):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        # Generally important variables
        added_number = 0

        # Code
        mongo.participants().delete_many({})
        for member in interaction.guild.members:
            add_player = {"_id": int(member.id),
                          "name": f"{member.display_name}",
                          "mention": f"{member.mention}",
                          "avatar": f"{member.display_avatar}"
                          }
            mongo.participants().insert_one(add_player)
            added_number += 1
        await interaction.response.send_message(f'{added_number} players added to the participant list.')

    # Removes a "participant" from the storage database
    @group.command(name='exclude', description='Exclude a player from the list of participants.')
    @app_commands.describe(player='Mention the player you wish to add. (Does not actually mention them)')
    @app_commands.guild_only()
    async def remove_user(self, interaction: discord.Interaction, player: discord.Member):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        # Generally important variables
        included = []

        # Code
        query = {"_id": player.id}
        check = mongo.participants().find(query)
        for inc in check:
            included.append(inc)
        if included:
            mongo.participants().delete_one(query)
            await interaction.response.send_message(f'{player.display_name} excluded.')
        elif not included:
            await interaction.response.send_message('Player is not in the participant list!')
        elif player is None:
            await interaction.response.send_message('Please specify a player!')

    # Removes ALL "participants" from the storage database
    @group.command(name='exclude_all', description='Exclude ALL players from the list of participants.')
    @app_commands.guild_only()
    async def remove_all_users(self, interaction: discord.Interaction):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        # Code
        clear_list = mongo.participants().delete_many({})
        await interaction.response.send_message(f'{clear_list.deleted_count} participants excluded.')

    # Custom message stuff
    # Show a list of all the custom messages!
    @group.command(name='message_list', description='Show a list of all the messages.')
    @app_commands.rename(message_type='type')
    @app_commands.describe(message_type='Pick a type of message to show a list of.')
    @app_commands.guild_only()
    async def message_list(self, interaction: discord.Interaction, message_type: typing.Literal['alive', 'dead']):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        # Generally important variables
        embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title='Message List')
        the_message = []
        temp_str = ''

        # Code
        if message_type == 'alive':
            if mongo.msg_alive().count_documents({}) > 0:
                for msg in mongo.msg_alive().find().sort("_id", 1):
                    the_message.append(msg)
                for final_message in the_message:
                    temp_str += f'{final_message["_id"]} | {final_message["message"]}\n'
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
                                temp_str += f'{another_temp_list[0][0]} | {another_temp_list[0][1]}\n'
                                another_temp_list.pop(0)
                                the_message.pop(0)
                        embed = embed.add_field(name='ID | Message', value=temp_str)
                        fields -= 1
                else:
                    embed = embed.add_field(name='ID | Message', value=temp_str)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message('The list is empty!')
        elif message_type == 'dead':
            if mongo.msg_dead().count_documents({}) > 0:
                for msg in mongo.msg_dead().find().sort("_id", 1):
                    the_message.append(msg)
                for final_message in the_message:
                    temp_str += f' {final_message["_id"]} | {final_message["message"]}\n'
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
                                temp_str += f'**{another_temp_list[0][0]}** | {another_temp_list[0][1]}\n'
                                another_temp_list.pop(0)
                                the_message.pop(0)
                        embed = embed.add_field(name='ID | Message', value=temp_str)
                        fields -= 1
                else:
                    embed = embed.add_field(name='ID | Message', value=temp_str)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message('The list is empty!')

    @group.command(name='message_add', description='Add a custom message for dying or living.')
    @app_commands.rename(message_type='type')
    @app_commands.describe(message_type='Type of message to add.',
                           message='Limit is 100 characters, including symbols and spaces')
    @app_commands.guild_only()
    async def message_add(self, interaction: discord.Interaction, message_type: typing.Literal['alive', 'dead'],
                          message: str):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        # Generally important variables
        message_id = 0
        find_message_id = []

        # Code
        if not len(message) > 100:
            if message_type == 'alive':
                while message_id <= 1000:
                    look_for = mongo.msg_alive().find({"_id": message_id})
                    for found_or_not in look_for:
                        find_message_id.append(found_or_not)
                    if len(find_message_id) < 1:
                        mongo.msg_alive().insert_one({"_id": message_id, "message": f"{message}"})
                        await interaction.response.send_message(
                            f'Added custom message to alive list with ID {message_id}.')
                        return
                    else:
                        message_id += 1
                        find_message_id.clear()
            elif message_type == 'dead':
                while message_id <= 1000:
                    look_for = mongo.msg_dead().find({"_id": message_id})
                    for found in look_for:
                        find_message_id.append(found)
                    if len(find_message_id) < 1:
                        mongo.msg_dead().insert_one({"_id": message_id, "message": f"{message}"})
                        await interaction.response.send_message(
                            f'Added custom message to dead list with ID {message_id}.')
                        return
                    else:
                        message_id += 1
                        find_message_id.clear()
        else:
            await interaction.response.send_message(f'Message too long!', ephemeral=True)

    @group.command(name='message_remove',
                   description='Remove a custom message, use the list command to learn a message\'s ID.')
    @app_commands.rename(message_id='id', message_type='type')
    @app_commands.describe(message_id='ID of the message being removed.', message_type='Type of message to remove/')
    @app_commands.guild_only()
    async def message_remove(self, interaction: discord.Interaction,
                             message_type: typing.Literal['alive', 'dead'], message_id: int):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        # Generally important variables
        deleted_message = []

        # Code
        if message_type == 'alive':
            if mongo.msg_alive().find_one({"_id": message_id}):
                for message in mongo.msg_alive().find({"_id": message_id}):
                    deleted_message.append(message)
                mongo.msg_alive().delete_one({"_id": message_id})
                for message in deleted_message:
                    await interaction.response.send_message(f'Message "{message["message"]}" has been deleted!')
            elif not mongo.msg_alive().find_one({"_id": message_id}):
                await interaction.response.send_message('Message does not exist!')
        elif message_type == 'dead':
            if mongo.msg_dead().find_one({"_id": message_id}):
                for message in mongo.msg_dead().find({"_id": message_id}):
                    deleted_message.append(message)
                mongo.msg_dead().delete_one({"_id": message_id})
                for message in deleted_message:
                    await interaction.response.send_message(f'Message "{message["message"]}" has been deleted!')
            elif not mongo.msg_dead().find_one({"_id": message_id}):
                await interaction.response.send_message('Message does not exist!')

    # TO-DO: ADD MORE DOCUMENTATION/COMMENTS, it will be hard to read otherwise soon enough
    # MORE TO-DO: Improve the code in general
    # EVEN MORE TO-DO: (not any time soon) Scoreboard and custom NPCs (for the loners out there).
    # NOT THE FINAL VERSION, this is more to see if I could, and in the future I will make a better
    # more feature rich one (probably, if I am not lazy)
    @group.command(name='start', description='Start hunger games!')
    @commands.guild_only()
    async def hunger_games(self, interaction: discord.Interaction):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
        # Default Messages
        default_alive = [
            {"message": "**Managed to live!**"}, {"message": "**Lived through a nuclear holocaust!**"},
            {"message": "**Had a nice day!**"}, {"message": "**Ran into a bunny, then ran for their life!**"},
            {"message": "**Thought it was a good idea to try and eat the bot. They succeeded!**"},
            {"message": "**Tried to run away from the cops, and then got high.**"}
        ]
        default_dead = [
            {"message": "*Tripped and snapped their neck.*"}, {"message": "*Insulted the owner of the discord.*"},
            {"message": "*Died due to pun overdose.*"}, {"message": "*Death by Snu Snu.*"},
            {"message": "*Got hit by a train, and then was finished off by a moose!*"},
            {"message": "*Had a lack of faith in J.C.*"},
            {"message": "*Thought it was a good idea to try and eat the bot. They failed.*"},
            {"message": "*Couldn't take it anymore.*"},
            {"message": "*Found some food, then found some food poisoning.*"},
            {"message": "*I've fallen, and I can't get up!*"}
        ]
        default_barely_survived = [
            {"message": "***Tripped, but fell on a pillow and survived!***"},
            {"message": "***Survived a heart attack!***"}
        ]

        # Generally important variables
        day = 1
        dead = []
        temp_day_dead = []

        # Adding all messages to one usable variable
        dead_msg = [db_message["message"] for db_message in list(mongo.msg_dead().find())]
        alive_msg = [db_message["message"] for db_message in list(mongo.msg_alive().find())]

        # Finds out where the use default messages or not
        for only_custom in [mongo.configs().find_one({"_id": 4})]:
            if not only_custom["only_custom_messages"]:
                dead_msg = [message["message"] for message in default_dead]
                alive_msg = [message["message"] for message in default_alive]
            elif only_custom["only_custom_messages"]:
                check_dead = list(mongo.msg_dead().find())
                check_alive = list(mongo.msg_alive().find())
                if len(check_dead) >= 1 <= len(check_alive):
                    break
                elif len(check_dead) < 1 <= len(check_alive):
                    await interaction.channel.send("No custom dead messages found, so using default.")
                    dead_msg = [message["message"] for message in default_dead]
                elif len(check_dead) >= 1 > len(check_alive):
                    await interaction.channel.send("No custom alive messages found, so using default.")
                    alive_msg = [message["message"] for message in default_alive]
                elif len(check_dead) < 1 > len(check_alive):
                    await interaction.channel.send("No custom messages found, so using defaults.")
                    dead_msg = [message["message"] for message in default_dead]
                    alive_msg = [message["message"] for message in default_alive]
        barely_survived_msg = [message["message"] for message in default_barely_survived]

        # CHECK IF THERE IS AT LEAST 2 PLAYERS
        player_count = mongo.participants().count_documents({}, limit=2)
        if player_count > 1:
            # Check if a game is already running
            currently_running = [mongo.configs().find_one({"_id": 1})]
            if not currently_running[0]["running"]:
                # The initial player list
                temp = ''
                player_list = mongo.participants().find()
                alive = [player for player in player_list]
                await interaction.response.send_message('Game starting with the following players!')
                for player in alive:
                    temp += f'{player["name"]}\n'
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

                        # A very lucky player!
                        else:
                            embed = discord.Embed(colour=discord.Colour.yellow(),
                                                  description=f'{npr.choice(barely_survived_msg)}')
                            await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                  icon_url=f'{participant["avatar"]}'))
                        await asyncio.sleep(2)
                    await asyncio.sleep(2)
                    for dead_player in temp_day_dead:
                        alive.remove(dead_player)
                    else:
                        temp_day_dead.clear()
                    if len(alive) > 1:
                        temp_la = ''
                        temp_ld = ''
                        for player in alive:
                            temp_la += f'{player["name"]}\n'
                        for player in dead:
                            temp_ld += f'*{player["name"]}*\n'
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

    @group.command(name='stop', description='Stop the current game at the end of the current day.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def hunger_games_stop(self, interaction: discord.Interaction):
        # MONGO
        mongo = MongoDB(discord_id=interaction.guild_id)
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
    await bot.add_cog(Hg(bot))
