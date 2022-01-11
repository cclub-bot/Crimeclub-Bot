import logging
import re
import random
import time

from cclub_bot.actions.actions import BaseAction
from cclub_bot.actions.bank import BankAction
from cclub_bot.reporter import Reporter
from cclub_bot.wrapper import RequestWrapper
from config2 import Config


class TraderAction(BaseAction):
    action = "smuggle"
    session = None
    trading_map = [
        {
            "location": "Los Angeles",
            "sell": {
                "drugs": ["3"],
                "drank": ["5"]
            },
            "buy": {
                "drugs": ["4"],
                "drank": ["2"]
            }
        },
        {
            "location": "Philadelphia",
            "sell": {
                "drugs": ["4"],
                "drank": ["2"]
            },
            "buy": {
                "drugs": ["5"],
                "drank": ["6"]
            }
        },
        {
            "location": "Austin",
            "sell": {
                "drugs": ["5"],
                "drank": ["6"]
            },
            "buy": {
                "drugs": ["3"],
                "drank": ["5"]
            }
        }
    ]

    def __init__(self):
        super(TraderAction, self).__init__()

    def trade_action(self, buy_type, buy_numbers, is_selling=False, limit=None):
        selector = "Verkoop" if is_selling else "Koop"
        self.session.get_uid_for(f"smuggle&type={buy_type}")

        get_page = self.session.action(
            action=self.action,
            args={"type": buy_type}
        )
        if not limit:
            if not is_selling:
                get_able = re.search(r'var able\s*=\s*(\d+)', get_page.text)
                if not get_able:
                    logging.warning("Unable to detect max amount of trade goods")
                    return False
                limit = int(get_able.group(1))
            else:
                get_amount_groups = re.findall(
                    r'(?s)<td class="inhoud".+?>\s*([\d,]+)\s*</td>.+?<input type="text" name="(.+?)"',
                    get_page.text
                )
                for entry in get_amount_groups:
                    if entry[1] == f"{buy_type}[{buy_numbers[0]}]":
                        limit = int(entry[0].replace(",", ""))
            if not limit:
                logging.warning("Unable to detect max amount of trade goods")
                return False
        if is_selling:
            get_action = re.search(
                '<input type="submit" name="(.+?)" value="Verkoop" />',
                get_page.text
            )
        else:
            get_action = re.search(
                '<input type="submit" name="(.+?)" value="Koop" />',
                get_page.text
            )

        get_secret = re.search(
            r"\.val\('(.+?)'\)\.attr\('name', '(.+?)'",
            get_page.text
        )
        post = {
            get_secret.group(2): get_secret.group(1),
            get_action.group(1).strip(): selector
        }
        build_data = {}
        for x in range(1, 7):
            build_data[f"{buy_type}[{x}]"] = str(limit) if str(x) in buy_numbers else ""
        time.sleep(2)
        build_data.update(post)
        get_capt = self.session.get_captcha_from_page(get_page.text)
        if get_capt:
            build_data.update(get_capt)
        if "captcha_code" in get_capt or "reload" in get_capt:
            self.do_captcha(get_capt, params={"type": buy_type})
            logging.info("Submitted captcha, retrying page")
            return self.trade_action(
                buy_type, buy_numbers, is_selling, limit
            )
        res = self.session.action(
            action=self.action,
            args={"type": buy_type},
            data=build_data
        )
        Reporter.report(
            module=self.__class__.__name__,
            action="trade",
            text=f"{selector} {buy_numbers} of {buy_type}"
        )

    def run(self, session: RequestWrapper, runs=3, retries=3):
        self.session = session
        for _ in range(runs):
            for action_todo in range(0, len(self.trading_map)):
                tried = 0
                while not FlightAction(session).travel_to(
                    location=self.trading_map[action_todo].get("location")
                ):
                    tried += 1
                    if tried == retries:
                        return False
                    logging.warning("Travel action failed, retrying")
                    new_action = None
                    if action_todo == 0:
                        new_action = len(self.trading_map)-1
                    else:
                        new_action = action_todo - 1
                    self.buy_sell_actions(new_action)
                    continue
                self.buy_sell_actions(action_todo)

    def buy_sell_actions(self, action_todo):
        buy = self.trading_map[action_todo]["buy"]
        sell = self.trading_map[action_todo]["sell"]
        BankAction(session=self.session).withdraw_amount(amount=1000000)
        for sell_type in sell:
            logging.debug("Selling %s", sell_type)
            self.trade_action(
                buy_type=sell_type,
                buy_numbers=sell[sell_type],
                is_selling=True
            )
        for buy_type in buy:
            logging.debug("Buying %s", buy_type)
            self.trade_action(
                buy_type=buy_type,
                buy_numbers=buy[buy_type],
                is_selling=False
            )
        BankAction(session=self.session).store_all()


class FlightAction:
    action = "traveling"
    session = None
    time_wait = 2 * 61
    ticket_price = 50000

    def __init__(self, session: RequestWrapper):
        self.session = session
        if Config().is_premium:
            self.time_wait = 61

    def do_captcha(self, params={}):
        params['captcha_check'] = "check"
        if "reload" in params:
            params[params["reload"]] = ""
        self.session.action(
            action=self.action,
            data=params
        )

    def travel_to(self, location):
        BankAction(session=self.session).withdraw_amount(self.ticket_price)
        self.session.get_uid_for(self.action)
        get_page = self.session.action(
            action=self.action
        )
        get_active = re.search(r'City: <b>(.+?)<', get_page.text)
        if get_active and get_active.group(1).strip() == location:
            return True

        locations = {}
        for x in re.findall(r"name='(.+?)' value='Reis naar (.+?)'", get_page.text):
            locations[x[1]] = x[0]
        if location not in locations:
            return False
        action_submit = locations[location]
        post = {action_submit: f"Reis naar {location}"}
        get_capt = self.session.get_captcha_from_page(get_page.text, has_to_reload=False)
        if get_capt:
            post.update(get_capt)
        if "code_traveling" in get_capt:
            self.do_captcha(get_capt)
            logging.info("Submitted captcha, retrying page")
            return self.travel_to(location=location)

        do_action = self.session.action(
            action=self.action,
            data=post
        )
        if "Je bent betrapt door de douane bij het smokkelen" in do_action.text:
            logging.warning("Got caught by customs")
            Reporter.report(
                module=self.__class__.__name__,
                action="travel",
                text=f"to {location} failed"
            )
            time.sleep(10)
            return False
        logging.info("Traveled to %s", location)
        Reporter.report(
            module=self.__class__.__name__,
            action="travel",
            text=f"to {location} success"
        )
        time.sleep(self.time_wait)
        return True
