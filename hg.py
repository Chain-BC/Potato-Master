import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands


# Hunger Games Module (Currently Placeholder)
class Hg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name='hg', description='All the subcommands for HG.')

    # Adds a "player" to participant_list.txt, each in a new line
    @group.command(name='include', description='Add a player to the list of participants.')
    async def add_user(self, interaction: discord.Interaction, player: discord.Member):
        with open('participant_list.txt', 'r') as main:
            for line in main:
                if f'{player.id}' not in line.strip('\n'):
                    continue
                else:
                    already_included = await interaction.response.send_message('Player has already been included!')
                    return already_included
        add_player = {
            "discordid": f"{player.id}",
            "name": f"{player.display_name}",
            "mention": f"{player.mention}",
            "guild": f"{interaction.guild_id}",
            "avatar": f"{player.display_avatar}",
            "dead": False
        }
        with open('participant_list.txt', 'a+') as ts:
            ts.write(f'{add_player}\n')
            ts.close()
        await interaction.response.send_message(f'Added {player.display_name} to participants!')

    # Removes a "player" from participant_list.txt, aka removes the line of where the id of the player is located in the file
    @group.command(name='exclude', description='Remove a player from the list of participants.')
    async def remove_user(self, interaction: discord.Interaction, player: discord.Member):
        with open('participant_list.txt', 'r') as main:
            with open('temp.txt', 'w') as output:
                exists = False
                for line in main:
                    if f'{player.id}' not in line.strip('\n'):
                        output.write(line)
                    else:
                        exists = True
                        await interaction.response.send_message(f'Removed {player.display_name} from participants!')
                if exists is False:
                    await interaction.response.send_message(f'That player is not in the participants list!')
        os.replace('temp.txt', 'participant_list.txt')

    # Clears the participant_list.txt file COMPLETELY (will probably limit to me being the only one able to in the future)
    @group.command(name='clear', description='Remove all players from the list of participants.')
    async def clear_players(self, interaction: discord.Interaction):
        with open('participant_list.txt', 'w') as ts:
            ts.truncate()
            ts.close()
        await interaction.response.send_message('Participants list cleared.')

    game_running = False

    # Starts the game with whatever players were included in the participant_list.txt file
    # NOT THE FINAL VERSION, this is more to see if I could, and in the future I will make a better, more feature rich one
    @group.command(name='start', description='Start hunger games, PLEASE SET IT UP FIRST!')
    async def hunger_games(self, interaction: discord.Interaction):
        day = 1
        alive = []
        # THE INITIAL PLAYER LIST
        with open('participant_list.txt', 'r') as player_list:
            for initiate in player_list:
                participant_list_add = eval(initiate)
                guild = interaction.guild_id
                if participant_list_add["guild"] == str(guild):
                    alive.append(participant_list_add)
                else:
                    continue
            embed = discord.Embed(colour=discord.Colour.green(), title='Participants')
            await interaction.response.send_message('Game starting with the following players!')
            for player in alive:
                with open('temp.txt', 'a') as ple:
                    ple.write(f'{player["name"]}\n')
            with open('temp.txt', 'r') as plist:
                await interaction.channel.send(embed=embed.add_field(name=f'1-{len(alive)}', value=plist.read()))
            os.remove('temp.txt')
            player_list.close()
        # THE ACTUAL GAME
        with open('participant_list.txt', 'r') as player_list:
            for line in player_list:
                await asyncio.sleep(3.5)
                participant = eval(line)
                embed1 = discord.Embed(colour=discord.Colour.blue())
                await interaction.channel.send(embed=embed1.set_author(name=f'{participant["name"]}', icon_url=f'{participant["avatar"]}'))


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Hg(bot))
