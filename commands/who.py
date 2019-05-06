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
        self.webclient = kwargs.get('webclient')
        self.debug = kwargs.get('debug', False)
        self.event = kwargs.get('payload').get('data')
        self.logger = logging.getLogger(__name__)
        self.arg_map = {'all': self.get_all, 'name': self.get_by_name, 'role': self.get_by_role}
        self.args = shlex.split(' '.join(kwargs.get('args')[1:]))
        if self.debug:
            self.logger.debug(self.args)

        self.name_map = defaultdict(list)
        self.title_map = defaultdict(list)
        self.build_data_maps()

    def build_data_maps(self):
        """ fill out data structures for querying by role and by name """
        members = self.webclient.users_list().get('members')
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
        """ return all member:role relationships """
        sb = ''
        for name, title in self.name_map.items():
            sb += '<@{}>: {}\n'.format(name, ' || '.join(title))
        self.send_message(sb, self.event.get('channel'))

    def get_by_name(self):
        """ return member:role relationship by looking up a name """
        if self.debug:
            self.logger.debug(self.name_map)
        self.send_message(' || '.join(self.name_map.get(self.args[1].lower())), self.event.get('channel'))

    def get_by_role(self):
        """ return member:role relationship by looking up a role """
        if self.debug:
            self.logger.debug('looking for {} in {}'.format(self.args, self.name_map))

        joined_args = ' '.join(self.args[1:]).lower()
        initial_result = self.title_map.get(joined_args) if self.title_map.get(joined_args) else list()

        for key, value in self.title_map.items():
            for arg in self.args:
                if not arg in key:
                    continue
                initial_result += self.title_map.get(key)
        if initial_result:
            initial_result = ['<@{}>'.format(x) for x in initial_result]
            self.send_message(' || '.join(set(initial_result)), self.event.get('channel'))
        else:
            self.send_message("No matches found.  If you think this is in error, try `who all`", self.event.get('channel'))

    def run(self):
        if not self.args:  # if they type `who` and nothing else, print help
            self.logger.debug(f'who command run without args')
            self.send_message(__doc__, self.event.get('channel'))
            return

        for arg in self.args:
            if self.debug:
                self.logger.debug('calling {}'.format(self.arg_map.get(arg, '!No Such Function!')))
            self.arg_map.get(arg, lambda: '')()
