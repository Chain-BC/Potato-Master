import os
import asyncio
import typing
import discord
import random
import pymongo
from discord import app_commands
from discord.ext import commands
from numpy import random as npr

# Database
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")


# Hunger Games Module
class Hg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name='hg', description='All the subcommands for HG.')

    @group.command(name='config', description='Tweak various options on the bot or repair it.')
    @app_commands.describe(option='Pick a value to change in the configurations or repair them.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction, option: typing.Literal['repair', 'only_custom_messages']):
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        configs_collection = guild_database["configs"]
        if option == 'repair':
            if not configs_collection.find_one({"_id": 0}):
                configs_collection.insert_one({"_id": 0, "guild": f"{interaction.guild.name}"})
            configs_collection.update_one({"running": {"$type": "bool"}},
                                          {"$set": {"_id": 1, "running": False}}, upsert=True)
            configs_collection.update_one({"stopping": {"$type": "bool"}},
                                          {"$set": {"_id": 2, "stopping": False}}, upsert=True)
            configs_collection.update_one({"force_stopping": {"$type": "bool"}},
                                          {"$set": {"_id": 3, "force_stopping": False}}, upsert=True)
            configs_collection.update_one({"only_custom_messages": {"$type": "bool"}},
                                          {"$set": {"_id": 4, "only_custom_messages": False}}, upsert=True)
            await interaction.response.send_message('Configs set back to default.')
        elif option == 'only_custom_messages':
            for true_or_false in [configs_collection.find_one({"_id": 4})]:
                if true_or_false["only_custom_messages"]:
                    configs_collection.update_one({"only_custom_messages": True},
                                                  {"$set": {"only_custom_messages": False}})
                    await interaction.response.send_message("Only custom messages disabled!")
                else:
                    configs_collection.update_one({"only_custom_messages": False},
                                                  {"$set": {"only_custom_messages": True}})
                    await interaction.response.send_message("Only custom messages enabled!")

    # Adds a "participant" to the database
    @group.command(name='include', description='Add a player to the list of participants.')
    @app_commands.describe(player='Mention the player you wish to add. (Does not actually mention them)')
    @app_commands.guild_only()
    async def add_user(self, interaction: discord.Interaction, player: discord.Member):
        # Generally important variables
        not_included = []
        # Database
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        participant_collection = guild_database["participant_list"]
        # Code
        query = {"_id": player.id}
        check = participant_collection.find(query)
        for not_inc in check:
            not_included.append(not_inc)
        if not not_included:
            add_player = {"_id": int(player.id),
                          "name": f"{player.display_name}",
                          "mention": f"{player.mention}",
                          "avatar": f"{player.display_avatar}"
                          }
            participant_collection.insert_one(add_player)
            await interaction.response.send_message(f'Added {player.display_name} to participants!')
        else:
            already_included = await interaction.response.send_message('Player has already been included!')
            return already_included

    # Adds all current guild members to the database
    @group.command(name='include_all', description='Add ALL players on the guild to the list of participants.')
    @app_commands.guild_only()
    async def add_all_users(self, interaction: discord.Interaction):
        # Generally important variables
        added_number = 0
        # Database
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        participant_collection = guild_database["participant_list"]
        # Code
        participant_collection.delete_many({})
        for member in interaction.guild.members:
            add_player = {"_id": int(member.id),
                          "name": f"{member.display_name}",
                          "mention": f"{member.mention}",
                          "avatar": f"{member.display_avatar}"
                          }
            participant_collection.insert_one(add_player)
            added_number += 1
        await interaction.response.send_message(f'{added_number} players added to the participant list.')

    # Removes a "participant" from the storage database
    @group.command(name='exclude', description='Exclude a player from the list of participants.')
    @app_commands.describe(player='Mention the player you wish to add. (Does not actually mention them)')
    @app_commands.guild_only()
    async def remove_user(self, interaction: discord.Interaction, player: discord.Member):
        # Generally important variables
        included = []
        # Database
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        participant_collection = guild_database["participant_list"]
        # Code
        query = {"_id": player.id}
        check = participant_collection.find(query)
        for inc in check:
            included.append(inc)
        if included:
            participant_collection.delete_one(query)
            await interaction.response.send_message(f'{player.display_name} excluded.')
        elif not included:
            await interaction.response.send_message('Player is not in the participant list!')
        elif player is None:
            await interaction.response.send_message('Please specify a player!')

    # Removes ALL "participants" from the storage database
    @group.command(name='exclude_all', description='Exclude ALL players from the list of participants.')
    @app_commands.guild_only()
    async def remove_all_users(self, interaction: discord.Interaction):
        # Database
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        participant_collection = guild_database["participant_list"]
        # Code
        clear_list = participant_collection.delete_many({})
        await interaction.response.send_message(f'{clear_list.deleted_count} participants excluded.')

    # Custom message stuff
    @group.command(name='message_list', description='Show a list of all the messages.')
    @app_commands.rename(message_type='type')
    @app_commands.describe(message_type='Pick a type of message to show a list of.')
    @app_commands.guild_only()
    async def message_list(self, interaction: discord.Interaction, message_type: typing.Literal['alive', 'dead']):
        # Generally important variables
        embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title='Message List')
        the_message = []
        # Database
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        db_messages_alive = guild_database["messages_alive"]
        db_messages_dead = guild_database["messages_dead"]
        # Code
        if message_type == 'alive':
            with open('temp_msg.txt', 'a', encoding='utf8') as msg_list:
                for msg in db_messages_alive.find().sort("_id", 1):
                    the_message.append(msg)
                for final_message in the_message:
                    msg_list.write(f' {final_message["_id"]} | {final_message["message"]}\n')
                msg_list.close()
            with open('temp_msg.txt', 'r', encoding='utf8') as msg_list:
                await interaction.response.send_message(embed=embed.add_field(name='ID | Message', value=msg_list.read()))
                msg_list.close()
            os.remove('temp_msg.txt')
        elif message_type == 'dead':
            with open('temp_msg.txt', 'a', encoding='utf8') as msg_list:
                for msg in db_messages_dead.find().sort("_id", 1):
                    the_message.append(msg)
                for final_message in the_message:
                    msg_list.write(f' {final_message["_id"]} | {final_message["message"]}\n')
                msg_list.close()
            with open('temp_msg.txt', 'r', encoding='utf8') as msg_list:
                await interaction.response.send_message(
                    embed=embed.add_field(name='ID | Message', value=msg_list.read()))
                msg_list.close()
            os.remove('temp_msg.txt')

    @group.command(name='message_add', description='Add a custom message for dying or living.')
    @app_commands.rename(message_type='type')
    @app_commands.describe(message_type='Type of message to add.')
    @app_commands.guild_only()
    async def message_add(self, interaction: discord.Interaction, message_type: typing.Literal['alive', 'dead'], message: str):
        # Generally important variables
        message_id = 0
        find_message_id = []
        # Database
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        db_messages_alive = guild_database["messages_alive"]
        db_messages_dead = guild_database["messages_dead"]
        # Code
        if message_type == 'alive':
            while message_id <= 1000:
                look_for = db_messages_alive.find({"_id": message_id})
                for found_or_not in look_for:
                    find_message_id.append(found_or_not)
                if len(find_message_id) < 1:
                    db_messages_alive.insert_one({"_id": message_id, "message": f"{message}"})
                    await interaction.response.send_message(f'Added custom message to alive list with ID {message_id}.')
                    return
                else:
                    message_id += 1
                    find_message_id.clear()
        elif message_type == 'dead':
            while message_id <= 1000:
                look_for = db_messages_dead.find({"_id": message_id})
                for found in look_for:
                    find_message_id.append(found)
                if len(find_message_id) < 1:
                    db_messages_dead.insert_one({"_id": message_id, "message": f"{message}"})
                    await interaction.response.send_message(f'Added custom message to dead list with ID {message_id}.')
                    return
                else:
                    message_id += 1
                    find_message_id.clear()

    @group.command(name='message_remove', description='Remove a custom message, use the list command to learn a message\'s ID.')
    @app_commands.rename(message_id='id', message_type='type')
    @app_commands.describe(message_id='ID of the message being removed.', message_type='Type of message to remove/')
    @app_commands.guild_only()
    async def message_remove(self, interaction: discord.Interaction,
                             message_type: typing.Literal['alive', 'dead'], message_id: int):
        # Generally important variables
        deleted_message = []
        # Database
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        db_messages_alive = guild_database["messages_alive"]
        db_messages_dead = guild_database["messages_dead"]
        # Code
        if message_type == 'alive':
            if db_messages_alive.find_one({"_id": message_id}):
                for message in db_messages_alive.find({"_id": message_id}):
                    deleted_message.append(message)
                db_messages_alive.delete_one({"_id": message_id})
                for message in deleted_message:
                    await interaction.response.send_message(f'Message "{message["message"]}" has been deleted!')
            elif not db_messages_alive.find_one({"_id": message_id}):
                await interaction.response.send_message('Message does not exist!')
        elif message_type == 'dead':
            if db_messages_dead.find_one({"_id": message_id}):
                for message in db_messages_dead.find({"_id": message_id}):
                    deleted_message.append(message)
                db_messages_dead.delete_one({"_id": message_id})
                for message in deleted_message:
                    await interaction.response.send_message(f'Message "{message["message"]}" has been deleted!')
            elif not db_messages_dead.find_one({"_id": message_id}):
                await interaction.response.send_message('Message does not exist!')

    # TO-DO: ADD MORE DOCUMENTATION/COMMENTS, it will be hard to read otherwise soon enough
    # MORE TO-DO: CUSTOM MESSAGES FROM DATABASE and improve the code in general, also improve discord message formatting
    # EVEN MORE TO-DO: (not any time soon) Scoreboard and custom NPCs (for the loners out there).
    # Starts the game with whatever players were included in the database
    # NOT THE FINAL VERSION, this is more to see if I could, and in the future I will make a better
    # more feature rich one (probably, if I am not lazy)
    @group.command(name='start', description='Start hunger games, PLEASE SET IT UP FIRST!')
    @commands.guild_only()
    async def hunger_games(self, interaction: discord.Interaction):
        # Database accessing variables
        # Individual Discord Storage
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        participant_collection = guild_database["participant_list"]
        configs_collection = guild_database["configs"]
        db_messages_alive = guild_database["messages_alive"]
        db_messages_dead = guild_database["messages_dead"]
        # Other Storage
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
            {"message": "***Tripped, but fell on a pillow and survived!***"}, {"message": "***Survived a heart attack!***"}
        ]
        # Default Messages + Database Messages will be stored here
        dead_msg = []
        alive_msg = []
        barely_survived_msg = []
        # Generally important variables
        day = 1
        alive = []
        dead = []
        temp_day_dead = []
        # Adding all messages to one usable variable
        for db_message in list(db_messages_dead.find()):
            dead_msg.append(db_message["message"])
        for db_message in list(db_messages_alive.find()):
            alive_msg.append(db_message["message"])
        # ================ Finds out where the use default messages or not =========================
        for only_custom in [configs_collection.find_one({"_id": 4})]:
            if not only_custom["only_custom_messages"]:
                for message in default_dead:
                    dead_msg.append(message["message"])
                for message in default_alive:
                    alive_msg.append(message["message"])
            elif only_custom["only_custom_messages"]:
                check_dead = list(db_messages_dead.find())
                check_alive = list(db_messages_alive.find())
                if len(check_dead) >= 1 <= len(check_alive):
                    break
                elif len(check_dead) < 1 <= len(check_alive):
                    await interaction.channel.send("No custom dead messages found, so using default.")
                    for message in default_dead:
                        dead_msg.append(message["message"])
                elif len(check_dead) >= 1 > len(check_alive):
                    await interaction.channel.send("No custom alive messages found, so using default.")
                    for message in default_alive:
                        alive_msg.append(message["message"])
                elif len(check_dead) < 1 > len(check_alive):
                    await interaction.channel.send("No custom messages found, so using defaults.")
                    for message in default_dead:
                        dead_msg.append(message["message"])
                    for message in default_alive:
                        alive_msg.append(message["message"])

        for message in default_barely_survived:
            barely_survived_msg.append(message["message"])
        # CHECK IF THERE IS AT LEAST 2 PLAYERS
        player_count = participant_collection.count_documents({}, limit=2)
        if player_count > 1:
            # Check if a game is already running
            currently_running = configs_collection.find({"_id": 1})
            # Check if there is already a game running
            for running in currently_running:
                currently_running = running
            if not currently_running["running"]:
                # The initial player list
                player_list = participant_collection.find()
                for player in player_list:
                    alive.append(player)
                embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title='Participants')
                await interaction.response.send_message('Game starting with the following players!')
                for player in alive:
                    with open('temp.txt', 'a', encoding='utf8') as starting_with:
                        starting_with.write(f'{player["name"]}\n')
                with open('temp.txt', 'r', encoding='utf8') as starting_with:
                    await interaction.channel.send(
                        embed=embed.add_field(name=f'1-{len(alive)}', value=starting_with.read()))
                os.remove('temp.txt')
                # THE ACTUAL GAME
                while len(alive) > 1:
                    # Set hunger games to RUNNING
                    running_current = {"running": False}
                    running_new = {"$set": {"running": True}}
                    configs_collection.update_one(running_current, running_new)
                    random.shuffle(alive)
                    await asyncio.sleep(2)
                    await interaction.followup.send(f'Day {day} is upon us!')
                    await asyncio.sleep(4)
                    temp_day_alive = len(alive)
                    # This determines the outcome for each player that is ALIVE
                    for participant in alive:
                        # Shuffles the messages
                        random.shuffle(dead_msg)
                        random.shuffle(alive_msg)
                        random.shuffle(barely_survived_msg)
                        outcome = npr.rand()
                        # Living outcome
                        if outcome > 0.505:
                            embed = discord.Embed(colour=discord.Colour.green(),
                                                  description=f'{alive_msg[0]}')
                            await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                  icon_url=f'{participant["avatar"]}'))
                        # Dying outcome
                        elif outcome < 0.495:
                            if temp_day_alive > 1:
                                embed = discord.Embed(colour=discord.Colour.from_rgb(135, 0, 0),
                                                      description=f'{dead_msg[0]}')
                                await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                      icon_url=f'{participant["avatar"]}'))
                                temp_day_dead.append(participant)
                                participant.update({"name": f'~~{participant["name"]}~~'})
                                dead.append(participant)
                                temp_day_alive -= 1
                            else:
                                embed = discord.Embed(colour=discord.Colour.yellow(),
                                                      description=f'***Barely scraped by!***')
                                await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                      icon_url=f'{participant["avatar"]}'))
                        # A very lucky player!
                        else:
                            embed = discord.Embed(colour=discord.Colour.yellow(),
                                                  description=f'{barely_survived_msg[0]}')
                            await interaction.channel.send(embed=embed.set_author(name=f'{participant["name"]}',
                                                                                  icon_url=f'{participant["avatar"]}'))
                        await asyncio.sleep(3)
                    await asyncio.sleep(2)
                    for dead_player in temp_day_dead:
                        alive.remove(dead_player)
                    else:
                        temp_day_dead.clear()
                    if len(alive) > 1:
                        embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title=f'Day {day} Summary')
                        with open('temp.txt', 'a', encoding='utf8') as temp_list:
                            for player in alive:
                                temp_list.write(f'{player["name"]}\n')
                            for player in dead:
                                temp_list.write(f'{player["name"]}\n')
                            temp_list.close()
                        with open('temp.txt', 'r', encoding='utf8') as temp_list:
                            total = len(alive) + len(dead)
                            await interaction.channel.send(embed=embed.add_field(name=f'1-{total}', value=temp_list.read()))
                            temp_list.close()
                        os.remove('temp.txt')
                        day += 1
                    # Check if the game is supposed to stop now
                    stopping = configs_collection.find({"_id": 2})
                    for currently_stopping in stopping:
                        stopping = currently_stopping
                    if stopping["stopping"]:
                        break
                stopping = configs_collection.find({"_id": 2})
                for currently_stopping in stopping:
                    stopping = currently_stopping
                if stopping["stopping"]:
                    running_current = {"running": True}
                    running_new = {"$set": {"running": False}}
                    configs_collection.update_one(running_current, running_new)
                    stopping_current = {"stopping": True}
                    stopping_new = {"$set": {"stopping": False}}
                    configs_collection.update_one(stopping_current, stopping_new)
                    await interaction.followup.send('Game stopping!')
                    return
                else:
                    running_current = {"running": True}
                    running_new = {"$set": {"running": False}}
                    configs_collection.update_one(running_current, running_new)
                    for winner in alive:
                        await interaction.channel.send(f'{winner["name"]} is the winner of this bout!')
            elif currently_running["running"]:
                await interaction.response.send_message('A game is currently running!')
        else:
            await interaction.response.send_message('Please include at least 2 players!')

    @group.command(name='stop', description='Stop the current game at the end of the current day.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def hunger_games_stop(self, interaction: discord.Interaction):
        # Database
        guild_database = mongo_client[f"storage_{interaction.guild_id}"]
        configs_collection = guild_database["configs"]
        # Code
        stopping = configs_collection.find({"_id": 2})
        running = configs_collection.find({"_id": 1})
        for currently_stopping in stopping:
            stopping = currently_stopping
        for currently_running in running:
            running = currently_running
        if not stopping["stopping"] and running["running"]:
            stopping_current = {"stopping": False}
            stopping_new = {"$set": {"stopping": True}}
            configs_collection.update_one(stopping_current, stopping_new)
            await interaction.response.send_message('Game ending at the end of the current day!')
        elif not stopping["stopping"] and not running["running"]:
            await interaction.response.send_message('No game is currently running!')
        elif stopping["stopping"]:
            await interaction.response.send_message('Game already stopping!')


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Hg(bot))
