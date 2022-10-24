import pymongo
import typing


# Main mongo class for everything related to Hunger Games
class MongoHG:
    def __init__(self, discord_id):
        self.discord_id = discord_id
        self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.guild_database = self.mongo_client[f"storage_{self.discord_id}"]

    def msg(self, msg_type: typing.Literal['alive', 'dead', 'wounded']):
        messages_collection = self.guild_database[f"messages_{msg_type}"]
        return messages_collection

    def configs(self):
        configs_collection = self.guild_database["configs"]
        return configs_collection

    def participants(self):
        participant_collection = self.guild_database["participant_list"]
        return participant_collection