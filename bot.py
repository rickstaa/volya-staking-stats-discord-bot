"""Staking stats update bot."""

import logging
import os
import re

from discord import Client, Intents
from discord.ext import tasks
from solana.publickey import PublicKey
from solana.rpc.api import Client as SolanaClient

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
STAKE_STATS_CHANNEL_ID = os.getenv("STAKE_STATS_CHANNEL_ID")
STATS_UPDATE_RATE = int(os.getenv("STATS_UPDATE_RATE", 10))

QUICKNODE_SOLANA_CLIENT = SolanaClient(os.getenv("QUICKNODE_REST_API_ENDPOINT"))


def get_staking_data():
    """Get staking data.

    Returns:
        float: The percentage of NFTs staked.
    """
    resp = QUICKNODE_SOLANA_CLIENT.get_account_info(
        PublicKey(os.getenv("STAKING_PROGRAM"))
    )
    print(resp)  # TODO: Find a way to decode the program data.
    return 10  # FIXME: Dummy value.


class StakingStatsUpdateBot(Client):
    """Staking stats update bot class."""

    async def on_ready(self):
        """Make sure staking stats channel exists when bot is ready."""
        logging.debug(f"Logged on as {self.user}!")

        # Check if stats channel exists.
        logging.debug(f"Checking if channel {STAKE_STATS_CHANNEL_ID} exists.")
        self._channel = self.get_channel(int(STAKE_STATS_CHANNEL_ID))
        if self._channel is None:
            logging.error(f"Channel {STAKE_STATS_CHANNEL_ID} not found.")
            return

        # Check if channel is the right type
        if self._channel.type.name != "voice":
            logging.error(f"Channel {STAKE_STATS_CHANNEL_ID} is not a voice channel.")
            return

        # Start updating stats.
        self.update_staking_stats.start()

    @tasks.loop(seconds=STATS_UPDATE_RATE)
    async def update_staking_stats(self):
        logging.debug("Updating staking stats.")

        # Check if stats channel still exists.
        if self._channel is None:
            logging.error(f"Channel {STAKE_STATS_CHANNEL_ID} not found")
            return

        # Read staking info.
        percent_staked = get_staking_data()

        # Change stake percentage number.
        channel_name = self._channel.name
        logging.debug(f"Current channel name: {channel_name}")
        if re.search(r"\d+%?", channel_name):  # Check if channel name has a number.
            logging.debug("Channel name already contains a number.")
            new_channel_name = re.sub(r"\d+%?", f"{percent_staked}%", channel_name)
        else:
            logging.debug("Channel name does not yet contain a number.")
            new_channel_name = channel_name.rstrip() + f": {percent_staked}%"
        logging.debug(f"Changing channel name to {new_channel_name}.")
        await self._channel.edit(name=new_channel_name)


if __name__ == "__main__":
    client = StakingStatsUpdateBot(intents=Intents.default())
    client.run(BOT_TOKEN)
