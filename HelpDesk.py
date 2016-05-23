import os
import time
import shlex
import signal
import inspect
import logging
import threading
import importlib

from configparser import ConfigParser

import slackclient


class HelpDesk:
    NOISE = ['reconnect_url', 'presence_change', 'hello', 'user_typing']

    def __init__(self, config):
        self.config = config
        self.debug = config.get('DEFAULT', 'debug').lower() == 'true'
        self.client = None
        self.logger = logging.getLogger(__name__)
        self.establish_connection()
        self.id = self.client.api_call('auth.test').get('user_id')
        self.threads = list()

        self.commands = dict()
        self.load_commands()

        self.known_rooms = set()
        self.load_known_rooms()

    def establish_connection(self):
        """ Create client connection to slack. """
        self.client = slackclient.SlackClient(self.config.get('DEFAULT', 'token'))
        self.client.rtm_connect()
        self.logger.info('HelpDesk connected to slack')

    def is_direct_msg(self, msg):
        """ Return if the event occurred within a direct message with the bot.

        :param msg: event from rtm_read()
        :return: bool
        """
        return msg.get('channel', None) and msg.get('channel') not in self.known_rooms

    def is_a_mention(self, msg):
        """ Return if the event was directed at the bot specifically (@helpdesk).

        :param msg: event from rtm_read()
        :return: bool
        """
        return self.id in msg.get('text', '')

    def load_commands(self, *args):
        """ Import each command module from ./commands and store them in a list """
        for cmd in os.listdir(self.config.get('DIRECTORIES', 'commands')):
            if cmd.startswith('__'):  # skip __init__.py
                continue
            try:
                if cmd.strip('.py') in self.commands:  # we already know about this module, reload instead of import
                    importlib.reload(self.commands[cmd.strip('.py')])
                    self.logger.info('reloaded module {}'.format(cmd.strip('.py')))
                    continue
                module = importlib.import_module('commands.{}'.format(cmd.strip('.py')))
            except ImportError as e:
                self.logger.error('failed to import {}'.format(cmd))
            else:
                self.logger.info('imported module {}'.format(cmd))
                self.commands[cmd.strip('.py')] = module

    def load_known_rooms(self):
        """ Caches all public and private rooms that HelpDesk knows about. """
        for pub_channel in self.client.api_call('channels.list', exclude_archived=1).get('channels', []):  # public
            if self.debug:
                self.logger.debug(pub_channel)

            if pub_channel.get('is_channel'):
                self.logger.info('adding {} as a known channel with id {}'.format(pub_channel.get('name'), pub_channel.get('id')))
                self.known_rooms.add(pub_channel.get('id'))

        for priv_channel in self.client.api_call('groups.list', exclude_archived=1).get('groups', []):  # private
            if self.debug:
                self.logger.debug(priv_channel)

            if priv_channel.get('is_group'):
                self.logger.info('adding {} as a known channel with id {}'.format(priv_channel.get('name'), priv_channel.get('id')))
                self.known_rooms.add(priv_channel.get('id'))

    def help(self, user, command='', *args):
        """ List out each command in ./commands and print their associated __doc__. """
        sb = ''
        if not command:
            sb += 'Hello <@{}>, I can provide help on the following commands (help [command])\n'.format(user)
            for cmd, module in self.commands.items():
                sb += '\t<@{}>: help {}\n'.format(self.id, cmd)
            return sb
        else:
            return self.commands.get(command).__doc__

    def loop(self):
        """ Main loop to handle event handling dispatch """
        if self.client:
            while True:
                for event in self.client.rtm_read():
                    type = event.get('type')

                    if type in HelpDesk.NOISE:  # don't process the noise
                        continue

                    if self.debug:  # log full events if debugging
                        self.logger.debug(event)

                    if type != 'message' or event.get('hidden'):  # skip things that arent message, and skip edits
                        continue

                    if not event.get('user') == self.id and self.is_direct_msg(event) or self.is_a_mention(event):
                        text = event.get('text').lstrip('<@{}>: '.format(self.id))
                        args = shlex.split(text)

                        if self.debug:
                            self.logger.debug('calling {}'.format(args))

                        if hasattr(self, args[0]):
                            response = getattr(self, args[0])(event.get('user'), *args[1:])
                            self.client.api_call('chat.postMessage', channel=event.get('channel'), text=response, as_user=True)
                        else:
                            for name, obj in inspect.getmembers(self.commands.get(args[0].lower(), [])):
                                if not name.startswith('__') and inspect.isclass(obj):
                                    if hasattr(obj, 'run'):
                                        kwargs = dict(locals(), **self.__dict__)  # build a new dict from both sets
                                        del(kwargs['self'])  # remove self to avoid problems
                                        inst_obj = obj(**kwargs)  # instantiate
                                        thread = threading.Thread(target=inst_obj.run, name=name)  # call .run
                                        self.threads.append(thread)
                                        thread.start()

                time.sleep(int(self.config.get('DEFAULT', 'sleep_interval')))
        else:
            err_msg = 'Connection Failed.  Invalid token?'
            self.logger.error(err_msg)
            print(err_msg)


if __name__ == '__main__':
    # read config
    config = ConfigParser()
    config.read('./config/botconfig.cfg')

    # set log level and log location
    logging.basicConfig(filename=config.get('LOGGING', 'log_name'), level='DEBUG',
                        format='%(asctime)s | %(name)s | %(module)s -%(lineno)4s | %(levelname) -8s | %(message)s')

    hd = HelpDesk(config)
    # sending a SIGHUP to the main bot process causes it to reload commands from disk
    signal.signal(signal.SIGHUP, hd.load_commands)

    hd.logger.info("HelpDesk starting up.")
    try:
        hd.loop()
    except KeyboardInterrupt:
        print('Cleaning up and shutting down')
        hd.logger.info("HelpDesk shutting down.")
    finally:
        # clean up actions if any
        for thread in hd.threads:
            thread.join()
        hd.logger.info("HelpDesk threads done.")


