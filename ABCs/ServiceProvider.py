"""
Abstract Base Class for general commands
"""


class ServiceProviderABC:
    def __init__(self, *args, **kwargs):
        pass

    def send_message(self, message, channel):
        self.client.api_call('chat.postMessage', channel=channel, text=message, as_user=True)

    def run(self, *args, **kwargs):
        raise NotImplementedError('Override run function.')
