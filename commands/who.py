"""
Doc statement
"""
import os
from ABCs import ServiceProvider


class Who(ServiceProvider.ServiceProviderABC):
    def __init__(self, *args, **kwargs):
        super(Who, self).__init__(*args, **kwargs)

    def run(self):
        print('Who command run')

if __name__ == '__main__':
    Who().run()


"""
import slackclient
import difflib
from collections import defaultdict
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