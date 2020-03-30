class LinkedInError(Exception):
    def __init__(self, msg, code=None):
        self.code = code or 0
        super().__init__(msg)

    @property
    def msg(self):
        return self.args[0]
