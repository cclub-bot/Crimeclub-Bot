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
    action = "stealvehicles"
    max_risk = 70
    min_risk = 35

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

    def run(self, session: RequestWrapper, second_run=False):
        session.get_uid_for(self.action)
        result = session.action(
            action=self.action
        )
        if "prison" in result.url:
            logging.warning("In prison, trying again in 5 seconds")
            time.sleep(5)
            return self.run(session)
        can_second_run = result.text.count('auto.png') == 2
        get_percentages = re.findall(
            r'(?s)name="action" value="(.+?)".+?inhoud_c">\s+(\d+)%',
            result.text
        )
        if not get_percentages:
            return False
        action_group = {}
        for x in get_percentages:
            action_group[int(x[0])] = int(x[1])

        action_todo = self.get_best_fit_action(action_group)
        get_post_action = re.search(
            r'<input type="submit" name="(.+?)"',
            result.text
        )
        if not get_post_action:
            return None
        post = {
            "action": action_todo,
            "mouse_easy": "1"
        }
        post.update(
            {get_post_action.group(1): "Uitvoeren"}
        )
        get_capt = session.get_captcha_from_page(result.text)
        if get_capt:
            post.update(get_capt)
        if "code_crime" in get_capt or "reload" in get_capt:
            self.do_captcha(get_capt, session=session)
            logging.info("Submitted captcha, retrying page")
            return self.run(session=session)
        do_action = session.action(
            action=self.action,
            data=post
        )
        if "maar je bent wel ontsnapt aan de politie" in do_action.text:
            logging.info("Carjack action failed, jailed, waiting")
            Reporter.report(
                module=self.__class__.__name__,
                action="result",
                text="failed"
            )
            time.sleep(10)

        elif "De poging is mislukt" in do_action.text:
            logging.info("Carjack action failed, ignoring")
            Reporter.report(
                module=self.__class__.__name__,
                action="result",
                text="jailed"
            )
        else:
            Reporter.report(
                module=self.__class__.__name__,
                action="result",
                text="success"
            )
        if not second_run:
            logging.info("Advanced carjack available (possibly), re-running action")
            return self.run(session=session, second_run=True)
        if GarageAction(session=session).sell_all(min_amount=4):
            BankAction(session=session).store_all()
        return True
