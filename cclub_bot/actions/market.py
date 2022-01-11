import logging
import re
import time

import cclub_bot.wrapper
from cclub_bot.reporter import Reporter
from cclub_bot.actions.bank import BankAction
from config2 import Config


class MarketAction:

    session = False
    max_to_spend = 50000000
    min_buy = 100
    create_offers = False

    def __init__(self, session: cclub_bot.wrapper.RequestWrapper):
        self.session = session

    def get_entry_for(self, row):
        if "Credits verkopen" not in row:
            return False
        get_cr = re.search(r'([\d,]+) credits', row)
        if not get_cr:
            return False
        num_credits = int(get_cr.group(1).replace(",", "").strip())
        get_ch = re.search(r'\$\s*([\d,]+)', row)
        if not get_ch:
            return False
        num_cash = int(get_ch.group(1).replace(",", "").strip())
        if num_credits >= self.min_buy and num_cash < self.max_to_spend:
            buy_action = re.search(r"name='(koop_\d+)'", row)
            if buy_action:
                if BankAction(session=self.session).banked >= num_cash:
                    Reporter.report(
                        module=self.__class__.__name__,
                        action="buy",
                        text=f"Buying {num_credits} credits for {num_cash}"
                    )
                    get_page = self.session.action(
                        action="market",
                        data={buy_action.group(1): "Koop"}
                    )
                    logging.info(f"Bought {num_credits} for {num_cash}")
                    return True
                logging.warning(f"Need {num_cash} for {num_credits} {buy_action.group(1)}")
        return False

    def sell_action(self):
        get_page = self.session.action(
            action="market",
            args={"add": "true", "tab": "credits"}
        )
        body = {
            "bbod": str(self.max_to_spend),
            "count": str(self.min_buy),
            "soort": "2",
            "anoniem": "1",
            "add": "Credits verkopen/aanvragen"
        }
        get_page = self.session.action(
            action="market",
            args={"add": "true", "tab": "credits"},
            data=body
        )
        logging.info("Created credit offer for %s -> %s", self.max_to_spend, self.min_buy)
        Reporter.report(
            module=self.__class__.__name__,
            action="buy",
            text=f"Created credit offer for {self.max_to_spend} -> {self.min_buy}"
        )
        return True

    def get_market(self):
        self.session.get_uid_for("market")
        get_page = self.session.action(
            action="market"
        )
        if "prison" in get_page.url:
            time.sleep(10)
            logging.warning("Jailed, retrying")
            return self.get_market()
        config = Config()
        if re.search(r'name="annuleren_\d+"', get_page.text):
            logging.warning("Not running market because sell entry is already available")
            return False
        if config.trading_accept_trades:
            get_koop_html = get_page.text.split("<b>Koop</b>")[1].split("</table>")[0]
            for entry in re.findall('(?s)<tr(.+?)</tr>', get_koop_html):
                check = self.get_entry_for(entry)
                if check:
                    return True
        if config.trading_create_trades:
            self.sell_action()
