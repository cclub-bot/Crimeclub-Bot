import logging
import re
import cclub_bot.wrapper
from cclub_bot.reporter import Reporter


class BankAction:

    session = False
    banked = 0
    cash = 0

    def __init__(self, session: cclub_bot.wrapper.RequestWrapper):
        self.session = session
        self.get_bank()

    def get_bank(self):
        self.session.get_uid_for(action="bank")

        overview = self.session.action(
            action="bank"
        )
        # self.session.get_captcha_from_page(text=overview.text)
        get_cash = re.search(
            r'(?s)getElementById\("currentCash.+?\.value\s*=\s*"(\d+)"',
            overview.text
        )
        if get_cash:
            self.cash = int(get_cash.group(1))

        get_bank = re.search(
            r'(?s)getElementById\("currentBank.+?\.value\s*=\s*"(\d+)"',
            overview.text
        )
        if get_bank:
            self.banked = int(get_bank.group(1))

    def store_all(self):
        self.session.action(
            action="bank",
            args={"tab": "bank"},
            data={
                "amount": str(self.cash),
                "act": "0",
                "submit_switch": "Geld Overzetten"
            }
        )
        Reporter.report(
            module=self.__class__.__name__,
            action="deposit",
            text=str(self.cash)
        )

    def store_amount(self, amount):
        if amount > self.cash:
            amount = self.cash
        self.session.action(
            action="bank",
            args={"tab": "bank"},
            data={
                "amount": str(amount),
                "act": "0",
                "submit_switch": "Geld Overzetten"
            }
        )
        Reporter.report(
            module=self.__class__.__name__,
            action="deposit",
            text=str(amount)
        )

    def withdraw_all(self):
        logging.info("Withdrawing %s from bank", self.cash)
        self.session.action(
            action="bank",
            args={"tab": "bank"},
            data={
                "amount": str(self.banked),
                "act": "1",
                "submit_switch": "Geld Overzetten"
            }
        )
        Reporter.report(
            module=self.__class__.__name__,
            action="withdraw",
            text=str(self.cash)
        )

    def withdraw_amount(self, amount):
        if amount > self.banked:
            logging.warning("Error withdrawing %s max is %s", amount, self.banked)
            return False
        logging.info("Withdrawing %s from bank", amount)
        self.session.action(
            action="bank",
            args={"tab": "bank"},
            data={
                "amount": str(amount),
                "act": "1",
                "submit_switch": "Geld Overzetten"
            }
        )
        Reporter.report(
            module=self.__class__.__name__,
            action="withdraw",
            text=str(amount)
        )
        return True

    def donate_familie(self, amount):
        self.session.get_uid_for("famdonate")
        res = self.session.action(
            action="famdonate"
        )
        self.session.action(
            action="famdonate",
            data={"amount": str(amount), "donate": "Doneer aan de familie!"}
        )

