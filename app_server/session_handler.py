from flask import session


class SessionHandler():

    def set_value(self, key, val):
        session[key] = val

    def get_value(self, key):
        return session.get(key) or None
