import os
import json

from Chainmail.Plugin import ChainmailPlugin
from Chainmail.Events import Events, PlayerConnectedEvent
from Chainmail.Player import Player
from Chainmail import Wrapper
import requests


class RemoteWhitelist(ChainmailPlugin):

    def __init__(self, manifest: dict, wrapper: "Wrapper.Wrapper"):
        super().__init__(manifest, wrapper)

        config_path = os.path.join(self.manifest["path"], "config.json")
        if not os.path.isfile(config_path):
            self.config = {
                "api_url": "http://localhost:8796",
                "kick_message": "You are not whitelisted on this server."
            }
            with open(config_path, "w") as f:
                json.dump(self.config, f, sort_keys=True, indent=4)
        else:
            with open(config_path) as f:
                self.config = json.load(f)

        self.wrapper.EventManager.register_handler(Events.PLAYER_CONNECTED, self.handle_player_joined)

    def check_player_whitelisted(self, player: Player) -> bool:
        try:
            resp = requests.get(self.config["api_url"] + "/auth", params={
                "uuid": player.uuid
            }).json()
            return resp.get("whitelisted", True)

        except requests.exceptions.ConnectionError:
            self.logger.error("Failed to contact remote server.")
            return True

    def handle_player_joined(self, event: PlayerConnectedEvent):
        whitelisted = self.check_player_whitelisted(event.player)
        if not whitelisted:
            self.logger.info(f"Player {event.player.username} was kicked for not being on the whitelist.")
            event.player.kick(self.config["kick_message"])
