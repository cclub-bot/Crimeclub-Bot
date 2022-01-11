import os
import json


class Config:
    data = {}

    def __init__(self):
        self.load_config()

    @property
    def username(self):
        return self.data.get("username")

    @property
    def password(self):
        return self.data.get("password")

    @property
    def session(self):
        return self.data.get("session")

    @property
    def max_captcha_attempt(self):
        return self.data.get("max_captcha_attempt")

    @property
    def min_bullets(self):
        return Config.convert(self.data["bullets"]["min_bullets"])

    @property
    def bullet_small_batch(self):
        return Config.convert(self.data["bullets"]["bullet_small_batch"])

    @property
    def bullet_small_batch_cash(self):
        return Config.convert(self.data["bullets"]["bullet_small_batch_cash"])

    @property
    def bullet_medium_batch(self):
        return Config.convert(self.data["bullets"]["bullet_medium_batch"])

    @property
    def bullet_medium_batch_cash(self):
        return Config.convert(self.data["bullets"]["bullet_medium_batch_cash"])

    @property
    def bullet_large_batch(self):
        return Config.convert(self.data["bullets"]["bullet_large_batch"])

    @property
    def bullet_large_batch_cash(self):
        return Config.convert(self.data["bullets"]["bullet_large_batch_cash"])

    @property
    def enable_smuggle(self):
        return self.data["smuggle"]["enable"]

    @property
    def always_do_smuggle(self):
        return self.data["smuggle"]["always_do_smuggle"]

    @property
    def smuggle_min_cash(self):
        return Config.convert(self.data["smuggle"]["smuggle_min_cash"])

    @property
    def smuggle_max_cash(self):
        return Config.convert(self.data["smuggle"]["smuggle_max_cash"])

    @property
    def enable_pimp(self):
        return self.data["pimp"]["enable"]

    @property
    def pimp_disable_if_bullets_below(self):
        return Config.convert(self.data["pimp"]["disable_if_bullets_below"])

    @property
    def trading_credit_amount(self):
        return Config.convert(self.data["trading"]["credit_amount"])

    @property
    def trading_min_cash_required(self):
        return Config.convert(self.data["trading"]["min_cash_required"])

    @property
    def trading_max_to_offer(self):
        return Config.convert(self.data["trading"]["max_to_offer"])

    @property
    def trading_accept_trades(self):
        return self.data["trading"]["accept_trades"]

    @property
    def trading_create_trades(self):
        return self.data["trading"]["create_trades"]

    @property
    def is_premium(self):
        return self.data["misc"]["is_premium"]

    @property
    def sleep_between_actions(self):
        return self.data["misc"]["sleep_between_actions"]

    @property
    def sleep_after_run(self):
        return self.data["misc"]["sleep_after_run"]

    def action_enabled(self, action):
        return self.data["actions"][action]

    def load_config(self):
        cfile = os.path.join(
            os.path.dirname(__file__),
            "config.json"
        )
        with open(cfile, "r") as f:
            self.data = json.load(f)

    @staticmethod
    def convert(string):
        string = str(string)
        try:
            return int(string)
        except:
            pass
        string = string.lower()
        if string.endswith("m"):
            return int(string[:-1]) * 1000000
        if string.endswith("k"):
            return int(string[:-1]) * 1000

    @staticmethod
    def get(key, default=None):
        attr = getattr(Config, key)
        if attr:
            return Config.convert(attr)
        return default

