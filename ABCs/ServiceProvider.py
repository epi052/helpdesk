"""
Abstract Base Class for general commands
"""


class ServiceProviderABC:
    def __init__(self, *args, **kwargs):
        self.name = None

    def run(self):
        raise NotImplementedError('Override run function.')
