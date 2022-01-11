import logging
import re
import time

from cclub_bot.actions.actions import BaseAction
from cclub_bot.actions.bank import BankAction
from cclub_bot.reporter import Reporter
from cclub_bot.wrapper import RequestWrapper


class CrimeAction(BaseAction):
    action = "crimes"
    max_risk = 70
    min_risk = 35

    def __init__(self):
        super(CrimeAction, self).__init__()

    def get_best_fit_action(self, actions):
        all_below = 0
        for action in actions:
            percentage = actions[action]
            if percentage < self.min_risk:
                all_below += 1
            if self.min_risk <= percentage <= self.max_risk:
                return action
        dict_keys = [x for x in actions]
        if all_below == len(actions):
            return dict_keys[0]
        return dict_keys[len(actions)-1]

    def run(self, session: RequestWrapper, second_run=False):
        can_second_run = False
        session.get_uid_for(self.action)
        result = session.action(
            action=self.action
        )
        if "prison" in result.url:
            logging.warning("In prison, trying again in 5 seconds")
            time.sleep(5)
            return self.run(session)
        get_percentages = re.findall(
            r'(?s)name="action" value="(.+?)".+?width="15%">\s+(\d+)%',
            result.text
        )
        if result.text.count('icons/gun.png') > 1:
            can_second_run = True
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
            "mouse_easy": "2",
            "mouse_hard": "2"
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
            logging.info("Crime action failed, jailed, waiting")
            Reporter.report(
                module=self.__class__.__name__,
                action="crime",
                text="failed"
            )
            time.sleep(5)

        elif "De misdaad is mislukt" in do_action.text:
            logging.info("Crime action failed, ignoring")
            Reporter.report(
                module=self.__class__.__name__,
                action="crime",
                text="jailed"
            )
        else:
            Reporter.report(
                module=self.__class__.__name__,
                action="crime",
                text="success"
            )
            BankAction(session=session).store_all()
        if can_second_run and not second_run:
            logging.info("Heavy crime available, re-running action")

            self.run(session=session, second_run=True)

        return True
