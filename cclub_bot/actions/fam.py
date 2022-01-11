import logging
import re
import random
import time

from cclub_bot.actions.actions import BaseAction
from cclub_bot.actions.bank import BankAction
from cclub_bot.actions.garage import GarageAction
from cclub_bot.reporter import Reporter
from cclub_bot.wrapper import RequestWrapper


class CarjackAction(BaseAction):
    action = "famcrimes"
    max_risk = 70
    min_risk = 35
    hireling_price = 1000000

    def __init__(self):
        super(CarjackAction, self).__init__()

    def get_best_fit_action(self, actions):
        all_below = 0
        dict_keys = [x for x in actions]
        # 10 percent chance to randomly select one
        if random.randint(0, 10) == 5:
            return random.choice(dict_keys)
        for action in actions:
            percentage = actions[action]
            if percentage < self.min_risk:
                all_below += 1
            if self.min_risk <= percentage <= self.max_risk:
                return action
        if all_below == len(actions):
            return dict_keys[0]
        return dict_keys[len(actions)-1]

    def get_huurlingen(self, current_amount, needed_amount=2):
        if current_amount >= needed_amount:
            return
        result = self.session.action(
            action="famhirelings"
        )
        to_buy = needed_amount - current_amount
        payload = {
            "amount": to_buy,
            "buyhirelings": "Koop!"
        }
        BankAction(session=self.session).withdraw_amount(
            amount=to_buy * self.hireling_price
        )
        result = self.session.action(
            action="famhirelings",
            data=payload
        )

    def run(self, session: RequestWrapper):
        self.session = session
        session.get_uid_for(self.action)
        result = session.action(
            action=self.action
        )
        get_huurlingen = re.search(
            r'heeft op dit moment <b>(\d+)</b> huurlingen',
            result.text
        )
        if not get_huurlingen:
            return False
        get_count = int(get_huurlingen.group(1))
        self.get_huurlingen(current_amount=get_count)
