import shlex
import inspect
import logging
import importlib
import threading

from pathlib import Path
from configparser import ConfigParser

import slack


class HelpDesk(slack.RTMClient):
    def __init__(self, config, *args, **kwargs):
        token = config.get("DEFAULT", "token")
        super(HelpDesk, self).__init__(token=token, *args, **kwargs)
        self.config = config
        self.threads = list()
        self.logger = logging.getLogger(__name__)
        self.debug = config.get("DEFAULT", "debug").lower() == "true"
        self.webclient = slack.WebClient(token=token)
        self.id = self.webclient.api_call("auth.test").get("user_id")

        self.commands = dict()
        self.load_commands()

        public_rooms = set(
            ch.get("id") for ch in self.webclient.channels_list().get("channels")
        )
        private_rooms = set(
            ch.get("id") for ch in self.webclient.groups_list().get("groups")
        )
        self.known_rooms = public_rooms.union(private_rooms)

        self.logger.info("HelpDesk initialized.")

    def load_commands(self, *args):
        """ Import each command module from ./commands and store them in a list """
        for cmd in Path(self.config.get("DIRECTORIES", "commands")).iterdir():
            if cmd.name.startswith("__"):  # skip __init__.py
                continue
            try:
                if (
                    cmd.name.strip(".py") in self.commands
                ):  # known module, reload instead of import
                    importlib.reload(self.commands[cmd.name.strip(".py")])
                    self.logger.info("reloaded module {}".format(cmd.name.strip(".py")))
                    continue
                module = importlib.import_module(
                    "commands.{}".format(cmd.name.strip(".py"))
                )
            except ImportError as e:
                self.logger.error("failed to import {}".format(cmd))
            else:
                self.logger.info("imported module {}".format(cmd))
                self.commands[cmd.name.strip(".py")] = module

    def help(self, user, command="", *args):
        """ List out each command in ./commands and print their associated __doc__. """
        sb = ""
        if not command:
            sb += "Hello <@{}>, I can provide help on the following commands (help [command]):\n".format(
                user
            )
            for cmd, module in self.commands.items():
                sb += "\t<@{}>: help {}\n".format(self.id, cmd)
            return sb
        else:
            return self.commands.get(command).__doc__

    @slack.RTMClient.run_on(event="message")
    def process_commands(**payload):
        from pprint import pprint;pprint(payload)
        text = payload.get("data").get("text")
        args = shlex.split(text)

        rtm_client = payload.get("rtm_client")

        if hasattr(rtm_client, args[0]):
            response = getattr(rtm_client, args[0])(
                payload.get("data").get("user"), *args[1:]
            )
            rtm_client.webclient.chat_postMessage(
                channel=payload.get("data").get("channel"), text=response, as_user=True
            )

        else:
            for name, obj in inspect.getmembers(
                rtm_client.commands.get(args[0].lower(), [])
            ):
                if not name.startswith("__") and inspect.isclass(obj):
                    if not hasattr(obj, "run"):
                        continue

                    kwargs = dict(
                        locals(), **rtm_client.__dict__
                    )  # build a new dict from both sets
                    del kwargs["rtm_client"]  # remove self to avoid problems
                    inst_obj = obj(**kwargs)  # instantiate
                    thread = threading.Thread(
                        target=inst_obj.run, name=name
                    )  # call .run
                    rtm_client.threads.append(thread)
                    thread.start()


if __name__ == "__main__":
    # read config
    config = ConfigParser()
    config.read("./configs/helpdesk.cfg")

    # set log level and log location
    logging.basicConfig(
        filename=config.get("LOGGING", "log_name"),
        level="DEBUG",
        format="%(asctime)s | %(name)s | %(module)s -%(lineno)4s | %(levelname) -8s | %(message)s",
    )

    hd = HelpDesk(config)
    hd.start()
