"""
Command:  who [role|name|all] [argument]
    role:  [argument] returns all members with [argument] role active in their profile
    name:  returns all roles listed for [argument] in their profile
    all:   returns all users and their associated roles
"""
import shlex
import logging
from collections import defaultdict

from ABCs import ServiceProvider


class Who(ServiceProvider.ServiceProviderABC):
    def __init__(self, *args, **kwargs):
        super(Who, self).__init__(*args, **kwargs)
        self.client = kwargs.get('client')
        self.debug = kwargs.get('debug', False)
        self.event = kwargs.get('event')
        self.logger = logging.getLogger(__name__)
        self.arg_map = {'all': self.get_all, 'name': self.get_by_name, 'role': self.get_by_role}
        self.args = shlex.split(' '.join(kwargs.get('args')[1:]))
        if self.debug:
            self.logger.debug(self.args)

        self.name_map = defaultdict(list)
        self.title_map = defaultdict(list)
        self.build_data_maps()

    def build_data_maps(self):
        members = self.client.api_call('users.list').get('members')
        for member in members:
            if not member.get('deleted') and not member.get('is_bot'):
                title = member.get('profile').get('title')
                name = member.get('name')
                if title:
                    for subtitle in title.split(','):
                        if self.debug:
                            self.logger.debug('name: {} -- subtitle {}'.format(name, subtitle))
                        self.name_map[name].append(subtitle.strip())
                        self.title_map[subtitle.strip().lower()].append(name)

    def get_all(self):
        sb = ''
        for name, title in self.name_map.items():
            sb += '<@{}>: {}\n'.format(name, ' || '.join(title))
        self.send_message(sb, self.event.get('channel'))

    def get_by_name(self):
        if self.debug:
            self.logger.debug(self.name_map)
        self.send_message(' || '.join(self.name_map.get(self.args[1].lower())), self.event.get('channel'))

    def get_by_role(self):
        if self.debug:
            self.logger.debug(self.name_map)
        ret_val = ['<@{}>'.format(x) for x in self.title_map.get(' '.join(self.args[1:]).lower())]
        self.send_message(' || '.join(ret_val), self.event.get('channel'))

    def run(self):
        if not self.args:
            self.send_message(__doc__, self.event.get('channel'))
            return

        for arg in self.args:
            if self.debug:
                self.logger.debug('calling {}'.format(self.arg_map.get(arg, '!No Such Function!')))
            self.arg_map.get(arg, lambda: '')()

if __name__ == '__main__':
    pass

"""
import slackclient
import difflib
import pprint
import time

# TODO: add image, knuckle helpdesk guy

data_map = defaultdict(list)

def update_data(sc):
    global data_map
    data_map = defaultdict(list)
    members = sc.api_call('users.list').get('members')
    if not members:
        return
    data_map = defaultdict(list)
    for member in members:
        title = member['profile'].get('title', None)
        if title:
            for subtitle in title.split(','):
                data_map["who is a {}".format(subtitle)].append(member)
                data_map["who are the {}s".format(subtitle)].append(member)
                data_map['whos a {}'.format(subtitle)].append(member)
                data_map["who's a {}".format(subtitle)].append(member)

if __name__ == '__main__':
    token = "nope"
    client = slackclient.SlackClient(token)

    update_data(client)
    #pprint.pprint(data_map)

    if client.rtm_connect():
        while True:
            eventlist = client.rtm_read()
            if not eventlist:
                continue
            for event in eventlist:
                if event.get('type') == 'message':
                    fuzzymatch = difflib.get_close_matches(event.get('text'), data_map.keys())
                    if not fuzzymatch:
                        continue
                    resp = client.api_call('im.open', user=event.get('user'))
                    if resp.get('ok'):
                        nameset = set()
                        channel = resp.get('channel').get('id')
                        answer = "In answer to '{}' I have the following possibilities:".format(event.get('text'))
                        for k,v in data_map.items():
                            if k in fuzzymatch:
                                for name in v:
                                    nameset.add((name.get('name'), k.split()[-1]))
                        for name, title in nameset:
                            answer += "\n\t{} is a {}".format(name, title)
                        #names = str(set([y.get('name') for x in map(data_map.get, fuzzymatch) for y in x]))
                        #names = str(set([y.get('name') for x in map(data_map.get, fuzzymatch[0]) for y in x]))
                        post_resp = client.api_call('chat.postMessage', channel=channel, text=answer)
                elif event.get('type') == 'user_change':
                    for title in map(str.strip, event.get('user').get('profile').get('title').split(',')):
                        fuzzymatch = difflib.get_close_matches('who {}'.format(title), data_map.keys())
                        if not fuzzymatch:
                            continue
                        update_data(client)
                        #pprint.pprint(data_map)
            time.sleep(1)
    else:
        print('Connection Failed, invalid token?')
"""