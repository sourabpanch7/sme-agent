import logging


class GenericDAO:
    def __init__(self):
        self.status = True

    def read_data(self, **kwargs):
        return self.status

    def transform_data(self, **kwargs):
        return self.status

    def write_data(self, **kwargs):
        return self.status
