import os
import time
import logging
import importlib
from configparser import ConfigParser

import slackclient

class HelpDesk:
    def __init__(self, config):
        self.config = config
        self.commands = list()
        self.logger = logging.getLogger(__name__)
        self.load_commands()
        self.establish_connection()

    def establish_connection(self):
        """ Create client connection to slack. """
        self.client = slackclient.SlackClient(self.config['DEFAULT']['token'])
        self.client.rtm_connect()

    def load_commands(self):
        """ Import each command module from ./commands and store them in a list """
        for cmd in os.listdir(self.config['DIRECTORIES']['commands']):
            if cmd.startswith('__'):  # skip __init__.py
                continue
            try:
                self.commands.append(importlib.import_module('commands.{}'.format(cmd.strip('.py'))))
                self.logger.info('imported {}'.format(cmd))
            except ImportError as e:
                self.logger.error('failed to import {}'.format(cmd))

    def help(self):
        """ List out each command in ./commands and print their associated __doc__. """
        for cmd in self.commands:
            #TODO: this will be a response to a user request for help eventually
            print(cmd.__name__, cmd.__doc__)

    def loop(self):
        if self.client:
            while True:
                for event in self.client.rtm_read():
                    type = event.get('type')
                time.sleep(int(self.config['DEFAULT']['sleep_interval']))
        else:
            self.logger.error('Connection Failed.  Invalid token?')



if __name__ == '__main__':
    # read config
    config = ConfigParser()
    config.read('./config/botconfig.cfg')

    #set log level and log location
    logging.basicConfig(filename=config['LOGGING']['log_name'], level='DEBUG',
                        format='%(asctime)s | %(name)s | %(module)s-%(lineno)4s | %(levelname)-8s | %(message)s')

    hd = HelpDesk(config)
    hd.loop()

