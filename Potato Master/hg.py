# Imports from local directories
from Mongo.Mongo import MongoHG
from HG.messages.default import default_alive, default_dead, default_wounded
# Other
import asyncio
import typing
import discord
import numpy as np
from discord import app_commands
from discord.ext import commands
from numpy import random as npr


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

    @messages_group.command(name='list', description='Show a list of all the messages in a category.')
    @app_commands.rename(message_category='category')
    @app_commands.describe(message_category='Category of messages.')
    async def message_list(self, interaction: discord.Interaction,
                           message_category: typing.Literal['alive', 'dead', 'wounded']):
        """
            A list of all the messages, but only one category can be shown at the time.
        """
        # MONGO
        messages = MongoHG(discord_id=interaction.guild_id).msg(message_category)

        # Gets the embed for each page of the list
        def page_embed(page_number: int):
            skip = (page_number - 1) * 20
            embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220),
                                  title=f'Message List ({message_category.upper()})')
            msg1 = ''
            msg2 = ''
            for i, msg_dict in enumerate(messages.find().sort("_id", 1).skip(skip).limit(20)):
                if i < 10:
                    msg1 = msg1 + f'[{msg_dict["_id"]}] {msg_dict["message"]}\n'
                else:
                    msg2 = msg2 + f'[{msg_dict["_id"]}] {msg_dict["message"]}\n'
            for count in range(2):
                if count == 0:
                    embed = embed.add_field(name='[ID] Message', value=msg1)
                elif msg2:
                    embed = embed.add_field(name='[ID] Message', value=msg2)
            else:
                embed.set_footer(text=f'Page {page_number}/{view.total_pages}')
                return embed

        # The view and buttons used to change pages
        class MessageList(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.page = 1
                self.total_pages = int(messages.count_documents({}) / 20 + 1)

            async def on_timeout(self) -> None:
                self.clear_items()
                await view.sent_message.edit(view=self)

            @discord.ui.button(label='Previous', style=discord.ButtonStyle.green)
            async def previous(self, interaction_b: discord.Interaction, button: discord.ui.Button):
                if interaction_b.user == interaction.user:
                    if self.page > 1:
                        self.page -= 1
                        await interaction_b.response.edit_message(embed=page_embed(self.page))
                    else:
                        await interaction_b.response.defer()

            @discord.ui.button(label='Next', style=discord.ButtonStyle.green)
            async def next(self, interaction_b: discord.Interaction, button: discord.ui.Button):
                if interaction_b.user == interaction.user:
                    if self.page < 5:
                        self.page += 1
                        await interaction_b.response.edit_message(embed=page_embed(self.page))
                    else:
                        await interaction_b.response.defer()

        # Runs the function and view class, and determines where the embed/buttons are sent or not
        view = MessageList()
        if messages.count_documents({}) / 20 >= 1:
            await interaction.response.send_message(embed=page_embed(1), view=view)
            view.sent_message = await interaction.original_response()
        elif 1 > messages.count_documents({}) / 20 > 0:
            await interaction.response.send_message(embed=page_embed(1))
        else:
            await interaction.response.send_message('List is empty!')

    @messages_group.command(name='add', description='Add a custom message to a category.')
    @app_commands.rename(message_category='category')
    @app_commands.describe(message_category='Category of messages.',
                           message='Limit is 96 characters, including symbols and spaces')
    async def message_add(self, interaction: discord.Interaction,
                          message_category: typing.Literal['alive', 'dead', 'wounded'],
                          message: str):
        """
            Add a new message to the database, could be either a message for dying playing, or living player.
        """
        # MONGO
        messages = MongoHG(discord_id=interaction.guild_id).msg(message_category)

        # Code
        if not len(message) > 96:
            if messages.count_documents({}) < 200:
                message_id = 0
                while message_id <= 199:
                    find_message_id = [found for found in messages.find({"_id": message_id})]
                    if find_message_id:
                        message_id += 1
                        find_message_id.clear()
                    else:
                        messages.insert_one({"_id": message_id, "message": f"{message}"})
                        await interaction.response.send_message(
                            f'Added custom message to {message_category} category with ID {message_id}.')
                        return
            else:
                await interaction.response.send_message(f'Messages limit for {message_category} category reached!')
        else:
            await interaction.response.send_message('Message too long!', ephemeral=True)

    @messages_group.command(name='remove',
                            description='Remove a custom message, use the message list subcommand to see a message\'s ID.')
    @app_commands.rename(message_id='id', message_category='category')
    @app_commands.describe(message_id='ID of the message being removed.', message_category='Category of messages.')
    async def message_remove(self, interaction: discord.Interaction,
                             message_category: typing.Literal['alive', 'dead', 'wounded'],
                             message_id: int):
        """
            Remove a message from the database, ID MUST BE USED! You cannot use the message itself to remove it.
        """
        # MONGO
        messages = MongoHG(discord_id=interaction.guild_id).msg(message_category)

        # Code
        if messages.find_one({"_id": message_id}):
            deleted_message = [messages.find_one({"_id": message_id})]
            messages.delete_one({"_id": message_id})
            await interaction.response.send_message(f'Message "{deleted_message[0]["message"]}" has been deleted!')
        else:
            await interaction.response.send_message('Message does not exist!')

    """

        THIS IS A SUBGROUP, MEANT FOR EVERYTHING RELATING TO CONFIGURATIONS! (This usually relates to the database)
        At the moment includes:
            /hg config repair
            /hg config only_custom_messages

    """
    configs_group = app_commands.Group(name='config', description='The config subgroup of hg.', guild_only=True,
                                       default_permissions=discord.Permissions.administrator)

    @configs_group.command(name='default', description='Sets all configurations to default, sometimes fixes problems.')
    async def config_repair(self, interaction: discord.Interaction):
        """
            Sets all major configurations to the default values.
        """
        # MONGO
        configs = MongoHG(discord_id=interaction.guild_id).configs()

        # Code
        hg_configs = [
            {"guild": interaction.guild.name},
            {"running": False},
            {"stopping": False},
            {"user_changeable": {
                "day_msg": 'Day {day} incoming!',
                "recover_msg": 'Has recovered from their wounds!',
                "revive_msg": 'Has revived!',
                "only_custom_messages": False
            }}
        ]
        for dictionary in hg_configs:
            query = tuple(dictionary.items())
            query = {f"{query[0][0]}": {"$exists": True}}
            configs.update_one(query, {"$set": dictionary}, upsert=True)

        await interaction.response.send_message('Configs set to default.')

    @configs_group.command(name='only_custom_messages', description='Toggle only custom messages shown in game.')
    async def config(self, interaction: discord.Interaction):
        """
            Toggles whether only custom messages are shown or not. When True if there are any custom messages in the
            database, only those will be displayed when a game starts. If for some reason the database for alive messages
            or dead messages is empty, the default messages will be used for that type of message. This is implemented
            in the main command.
        """
        # MONGO
        configs = MongoHG(discord_id=interaction.guild_id).configs()

        # Code
        if configs.find_one({"user_changeable": {"$exists": True}})["only_custom_messages"]:
            configs.update_one({"only_custom_messages": True}, {"$set": {"only_custom_messages": False}})
            await interaction.response.send_message("Only custom messages disabled!")
        else:
            configs.update_one({"only_custom_messages": False}, {"$set": {"only_custom_messages": True}})
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
        participants = MongoHG(discord_id=interaction.guild_id).participants()

        # Generally important variables
        not_included = []

        # Code
        check = participants.find({"_id": user.id})
        for not_inc in check:
            not_included.append(not_inc)
        if not not_included:
            add_user = {
                "_id": int(user.id),
                "user": {
                    "nickname": f"{user.display_name}",
                    "avatar": f"{user.display_avatar}"
                },
                "status": {
                    "alive": True,
                    "wounded": False
                }
            }
            participants.insert_one(add_user)
            await interaction.response.send_message(f'Added {user.display_name} to the list of participants!')
        else:
            already_included = await interaction.response.send_message('User has already been included!')
            return already_included

    @participants_group.command(name='include_all',
                                description='Update/add ALL users on the guild to the list of participants.')
    async def participants_include_all(self, interaction: discord.Interaction):
        """
            Adds ALL users in the guild to the list of participants that can currently take part in the game.
        """
        # MONGO
        participants = MongoHG(discord_id=interaction.guild_id).participants()

        # Generally important variables
        added_number = 0

        # Code
        participants.delete_many({})
        for user in interaction.guild.members:
            add_user = {
                "_id": int(user.id),
                "user": {
                    "nickname": f"{user.display_name}",
                    "avatar": f"{user.display_avatar}"
                },
                "status": {
                    "alive": True,
                    "wounded": False
                }
            }
            participants.insert_one(add_user)
            added_number += 1
        await interaction.response.send_message(f'{added_number} users added/updated.')

    @participants_group.command(name='exclude', description='Exclude a user from the list of participants.')
    @app_commands.describe(user='Mention the user you wish to remove. (Does not actually mention them)')
    async def participants_exclude(self, interaction: discord.Interaction, user: discord.Member):
        """
            Removes a single user from the database containing all the participants.
        """
        # MONGO
        participants = MongoHG(discord_id=interaction.guild_id).participants()

        # Generally important variables
        included = []

        # Code
        check = participants.find({"_id": user.id})
        for inc in check:
            included.append(inc)
        if included:
            participants.delete_one({"_id": user.id})
            await interaction.response.send_message(f'{user.display_name} excluded.')
        else:
            await interaction.response.send_message('User is not in the participant list!')

    @participants_group.command(name='exclude_all', description='Exclude ALL users from the list of participants.')
    async def participants_exclude_all(self, interaction: discord.Interaction):
        """
            Removes ALL users from the database containing all the participants.
        """
        # MONGO
        participants = MongoHG(discord_id=interaction.guild_id).participants()

        # Code
        clear_list = participants.delete_many({})
        await interaction.response.send_message(f'{clear_list.deleted_count} users excluded.')

    """

        THIS IS THE REST OF THE COMMANDS, PART OF THE MAIN GROUP!
        At the moment includes:
            /hg start
            /hg stop

    """

    # TO-DO: Improve the code in general (IN PROGRESS)
    # MORE TO-DO: (not any time soon) Scoreboard and custom NPCs (for the loners out there).
    # NOT THE FINAL VERSION, this is more to see if I could, and in the future I will make a better
    # more feature rich one (probably, if I am not lazy)
    @app_commands.command(name='start', description='Start the hunger games!')
    @commands.guild_only()
    async def hunger_games(self, interaction: discord.Interaction):
        """
            Starts the game.
        """

        # Dealing with the interaction later.
        await interaction.response.defer()

        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)
        participants = mongo.participants()
        configs = mongo.configs()

        if participants.count_documents({}) >= 2:  # Minimum 2 players condition met
            if not configs.find_one({"running": {"$exists": True}})["running"]:  # Game running = FALSE
                """
                    SETUP
                """
                # Generally Important Variables
                day = 1

                # Gets all custom messages from the database
                alive_msg = np.array([db_message["message"] for db_message in mongo.msg('alive').find()])
                dead_msg = np.array([db_message["message"] for db_message in mongo.msg('dead').find()])
                wounded_msg = np.array([db_message["message"] for db_message in mongo.msg('wounded').find()])

                # Finds out where the use default messages or not (stored in HG/default.py as variables)
                if configs.find_one({"user_changeable": {"$exists": True}})["user_changeable"]["only_custom_messages"]:
                    if mongo.msg('alive').count_documents({}) == 0:
                        alive_msg = np.concatenate((alive_msg, default_alive), axis=None)
                        await interaction.channel.send('Alive messages category empty, so using default.')
                    if mongo.msg('dead').count_documents({}) == 0:
                        dead_msg = np.concatenate((dead_msg, default_dead), axis=None)
                        await interaction.channel.send('Dead messages category empty, so using default.')
                    if mongo.msg('wounded').count_documents({}) == 0:
                        await interaction.channel.send('Wounded messages category empty, so using default.')
                        wounded_msg = np.concatenate((wounded_msg, default_wounded), axis=None)
                else:  # Only custom messages = FALSE
                    alive_msg = np.concatenate((alive_msg, default_alive), axis=None)
                    dead_msg = np.concatenate((dead_msg, default_dead), axis=None)
                    wounded_msg = np.concatenate((wounded_msg, default_wounded), axis=None)

                # Gets all the players from the database
                participant_list = [participant for participant in participants.find()]  # Gets all players
                participant_list = np.array(participant_list)  # Turns the list to a numpy array
                for i, dictionary in enumerate(participant_list):  # Gives each player their own unique participant #
                    dictionary["participant_number"] = i + 1
                    participant_list[i] = dictionary
                players_alive = len(participant_list)  # Count of all players

                """
                    Starting the game (VERY SIMPLE TRUST ME)
                """
                # Set running to true in MongoDB
                configs.update_one({"running": False}, {"$set": {"running": True}})

                # This sends the initial participant list
                async def list_of_players(player_dictionary_list: np.ndarray, embed_title: str):
                    # Don't feel like commenting this, basically sends messages, each with an embed/multiple embeds
                    # containing a list of players.
                    player_dictionary_list_copy = np.copy(player_dictionary_list)
                    total_players = len(player_dictionary_list_copy)
                    embeds = int((total_players / 26 + 1) / 6 + 1)
                    number_of_messages = int(embeds / 2 + 1)
                    player_dictionary_list_copy.resize([number_of_messages, 2, 6, 26])
                    for current_message in player_dictionary_list_copy:
                        embed_list = []
                        for current_embed in current_message:
                            list_embed = discord.Embed(colour=discord.Colour.from_rgb(0, 130, 220), title=embed_title)
                            for current_field in current_embed:
                                list_players = ''
                                for current_player in current_field:
                                    if type(current_player) is dict:
                                        list_players += f'[{current_player["participant_number"]}]' \
                                                        f' {current_player["user"]["nickname"]}\n'
                                    else:
                                        break
                                if list_players != '':
                                    list_embed.add_field(name='Participant #', value=list_players)
                                else:
                                    break
                            if list_embed.fields:
                                embed_list.append(list_embed)
                            else:
                                break
                        await interaction.followup.send(embeds=embed_list)
                        await asyncio.sleep(1)
                starting_list_message = 'Game starting with the following players: '
                await list_of_players(participant_list, starting_list_message)

                """
                    Logic of the game using loops!
                """
                while players_alive > 1:
                    # Sends the current day
                    await asyncio.sleep(5)
                    day_msg: str = configs.find_one({"user_changeable": {"$exists": True}})["user_changeable"][
                        "day_msg"]
                    await interaction.followup.send(f'{day_msg.format(day=day)}')

                    for index, player in enumerate(npr.permutation(participant_list)):
                        # Outcome percentages
                        # In case you don't know what the decimals mean somehow:
                        # EXAMPLE: 0.52 = 52%, 0.44 = 44%, 0.04 = 4% and it all MUST add up to 100% (1.0 in decimals)
                        outcome = npr.choice(['alive', 'dead', 'wounded'], p=[0.52, 0.44, 0.04])

                        # YOUR FATE HAS BEEN CHOSEN!
                        if player["status"]["alive"]:  # Player is alive = TRUE
                            await asyncio.sleep(3)
                            if not player["status"]["wounded"]:  # Player is wounded = FALSE
                                """
                                    Normal outcomes for live players, 'alive', 'dead', and 'wounded'
                                """
                                if outcome == 'alive':  # Do nothing and send a random ALIVE message
                                    embed = discord.Embed(color=discord.Color.green(),
                                                          description=f'{npr.choice(alive_msg)}')
                                    await interaction.channel.send(
                                        embed=embed.set_author(name=f'{player["user"]["nickname"]}',
                                                               icon_url=f'{player["user"]["avatar"]}'))
                                elif outcome == 'dead':  # Player status alive = FALSE, send random DEAD message
                                    if players_alive > 1:  # There is at least 2 players alive
                                        embed = discord.Embed(color=discord.Color.from_rgb(135, 0, 0),
                                                              description=f'{npr.choice(dead_msg)}')
                                        embed.set_author(name=f'{player["user"]["nickname"]}',
                                                         icon_url=f'{player["user"]["avatar"]}')
                                        await interaction.channel.send(embed=embed)
                                        player["user"]["nickname"] = f'~~{player["user"]["nickname"]}~~'
                                        player["status"]["alive"] = False  # Player is not alive
                                        actual_index = next(i for i, og_player in enumerate(participant_list) if
                                                            og_player["_id"] == player["_id"])
                                        participant_list[actual_index] = player
                                        players_alive -= 1
                                    else:  # Only one player alive
                                        # Tie outcome percentages
                                        tie_outcome = npr.choice(['alive', 'tie'], p=[0.99985, 0.00015])

                                        if tie_outcome == 'alive':  # Last player alive LIVES!
                                            embed = discord.Embed(color=discord.Color.green(),
                                                                  description=f'{npr.choice(alive_msg)}')
                                            embed.set_author(name=f'{player["user"]["nickname"]}',
                                                             icon_url=f'{player["user"]["avatar"]}')
                                            await interaction.channel.send(embed=embed)
                                        else:  # Last player alive dies! Leading to a tie!
                                            embed = discord.Embed(color=discord.Color.from_rgb(135, 0, 0),
                                                                  description=f'{npr.choice(dead_msg)}')
                                            embed.set_author(name=f'{player["user"]["nickname"]}',
                                                             icon_url=f'{player["user"]["avatar"]}')
                                            await interaction.channel.send(embed=embed)
                                            player["user"]["nickname"] = f'~~{player["user"]["nickname"]}~~'
                                            player["status"]["alive"] = False
                                            actual_index = next(i for i, og_player in enumerate(participant_list) if
                                                                og_player["_id"] == player["_id"])
                                            participant_list[actual_index] = player
                                            players_alive -= 1
                                elif outcome == 'wounded':
                                    # Player status wounded = TRUE, send a random WOUNDED message
                                    embed = discord.Embed(color=discord.Color.yellow(),
                                                          description=f'{npr.choice(wounded_msg)}')
                                    embed.set_author(name=f'{player["user"]["nickname"]}',
                                                     icon_url=f'{player["user"]["avatar"]}')
                                    await interaction.channel.send(embed=embed)
                                    player["status"]["wounded"] = True
                                    actual_index = next(i for i, og_player in enumerate(participant_list) if
                                                        og_player["_id"] == player["_id"])
                                    participant_list[actual_index] = player
                            else:  # Player is wounded = TRUE
                                """
                                    Outcomes for wounded players, 'recover' and 'dead'
                                """
                                # Recovery from wound outcome percentages
                                recover_outcome = npr.choice(['recover', 'dead'], p=[0.2, 0.8])

                                if recover_outcome == 'recover':
                                    # Player status wounded = FALSE, send changeable RECOVERY message
                                    search = {"user_changeable": {"$exists": True}}
                                    recover_msg = configs \
                                        .find_one(search)["user_changeable"]["recover_msg"]
                                    embed = discord.Embed(color=discord.Color.yellow(), description=recover_msg)
                                    embed.set_author(name=f'{player["user"]["nickname"]}',
                                                     icon_url=f'{player["user"]["avatar"]}')
                                    await interaction.channel.send(embed=embed)
                                    player["status"]["wounded"] = False
                                    actual_index = next(i for i, og_player in enumerate(participant_list) if
                                                        og_player["_id"] == player["_id"])
                                    participant_list[actual_index] = player
                                else:
                                    # Player status alive = FALSE (but keep wounded = TRUE), send random DEAD message
                                    embed = discord.Embed(colour=discord.Colour.from_rgb(135, 0, 0),
                                                          description=f'{npr.choice(dead_msg)}')
                                    embed.set_author(name=f'{player["user"]["nickname"]}',
                                                     icon_url=f'{player["user"]["avatar"]}')
                                    await interaction.channel.send(embed=embed)
                                    player["user"]["nickname"] = f'~~{player["user"]["nickname"]}~~'
                                    player["status"]["alive"] = False
                                    actual_index = next(i for i, og_player in enumerate(participant_list) if
                                                        og_player["_id"] == player["_id"])
                                    participant_list[actual_index] = player
                                    players_alive = players_alive - 1
                        else:  # Player is alive = FALSE
                            """
                                Outcome for the really lucky dead players (.015% chance to revive!)
                            """
                            # Revive outcome percentages
                            revive_outcome = npr.choice(['revive', 'stay_dead'], p=[0.00015, 0.99985])

                            if revive_outcome == 'revive':  # Player status alive = True, send changeable REVIVE message
                                await asyncio.sleep(3)
                                revive_msg = \
                                    configs.find_one({"user_changeable": {"$exists": True}})["user_changeable"][
                                        "revive_msg"]
                                embed = discord.Embed(color=discord.Color.yellow(),
                                                      description=revive_msg)
                                embed.set_author(name=f'{player["user"]["nickname"]}',
                                                 icon_url=f'{player["user"]["avatar"]}')
                                await interaction.channel.send(embed=embed)
                                player["user"]["nickname"] = player["user"]["nickname"].strip('~')
                                player["status"]["alive"] = True
                                actual_index = next(i for i, og_player in enumerate(participant_list) if
                                                    og_player["_id"] == player["_id"])
                                participant_list[actual_index] = player
                                players_alive = players_alive + 1
                    """
                        After the for loop ends (All players have had their outcome decided)
                    """
                    if configs.find_one({"stopping": True}):
                        # Breaks the loop if game is stopping
                        break
                    elif players_alive > 1:
                        # This sends the summary of players alive/dead for the day
                        # TO-DO: Remove dead players from the summary after they have showed up once
                        await asyncio.sleep(5)
                        day_summary_msg = f'Day {day} Summary: '
                        await list_of_players(participant_list, day_summary_msg)
                        day = day + 1
                """
                    After the while loop ends, determines whether there is a winner or not (Or if the game is stopping)
                """
                if configs.find_one({"stopping": True}):  # If game is stopping
                    await asyncio.sleep(2.5)
                    await interaction.followup.send('Game is stopping.')
                    # This sends the final summary
                    await asyncio.sleep(1)
                    day_summary_msg = 'Final Summary: '
                    await list_of_players(participant_list, day_summary_msg)
                    # Set running to false in MongoDB
                    configs.update_one({"running": True}, {"$set": {"running": False}})
                    configs.update_one({"stopping": True}, {"$set": {"stopping": False}})
                else:
                    if players_alive == 0:  # There is no players alive
                        await asyncio.sleep(2.5)
                        await interaction.followup.send('It was a TIE!')
                        # This sends the final summary
                        await asyncio.sleep(1)
                        day_summary_msg = 'Final Summary: '
                        await list_of_players(participant_list, day_summary_msg)
                        # Set running to false in MongoDB
                        configs.update_one({"running": True}, {"$set": {"running": False}})
                    else:  # There is one player alive
                        winner = None
                        for player in participant_list:
                            if player["status"]["alive"] is True:
                                winner = player
                        await asyncio.sleep(2.5)
                        await interaction.followup.send(f'{winner["user"]["nickname"]} has won the hunger games!')
                        # This sends the final summary
                        await asyncio.sleep(1)
                        day_summary_msg = 'Final Summary: '
                        await list_of_players(participant_list, day_summary_msg)
                        # Set running to false in MongoDB
                        configs.update_one({"running": True}, {"$set": {"running": False}})
                    """
                        IF GAME RAN, THIS IS THE END
                    """
            else:  # Game running = TRUE
                await interaction.followup.send('A game is currently running!')
        else:  # Minimum 2 players condition NOT met
            await interaction.followup.send('Please include at least 2 players!')

    @app_commands.command(name='stop', description='Stop the current game at the end of the current day.')
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def hunger_games_stop(self, interaction: discord.Interaction):
        # MONGO
        mongo = MongoHG(discord_id=interaction.guild_id)
        # Code
        stopping = mongo.configs().find_one({"stopping": {"$exists": True}})
        running = mongo.configs().find_one({"running": {"$exists": True}})
        if not stopping["stopping"] and running["running"]:
            stopping_current = {"stopping": False}
            stopping_new = {"$set": {"stopping": True}}
            mongo.configs().update_one(stopping_current, stopping_new)
            await interaction.response.send_message('Game ending at the end of the current day!')
        elif not stopping["stopping"] and not running["running"]:
            await interaction.response.send_message('No game is currently running!')
        elif stopping["stopping"]:
            await interaction.response.send_message('Game already stopping!')


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(HG(bot))
