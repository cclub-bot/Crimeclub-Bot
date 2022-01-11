import random
import sys
import time
import logging
import coloredlogs
import importlib
import config

from cclub_bot.actions.bank import BankAction
from cclub_bot.reporter import Reporter
from cclub_bot.wrapper import RequestWrapper
from cclub_bot.actions.misdaadaction import CrimeAction
from cclub_bot.actions.carjack import CarjackAction
from cclub_bot.actions.pimpaction import PimpAction
from cclub_bot.actions.killbot import Murdering
from cclub_bot.actions.jail import BreakoutAction
from cclub_bot.actions.trader import TraderAction
from cclub_bot.actions.market import MarketAction
from cclub_bot.actions.pimpaction import Holiday
from cclub_bot.actions.hospital import StatusGrabber
from config2 import Config

coloredlogs.install(level=logging.DEBUG, stream=sys.stdout)


class Bot:
    wrapper = None
    config = None

    def __init__(self, login=False):
        self.config = Config()
        self.wrapper = RequestWrapper()
        #self.wrapper.auth(
        #    username=Config.username,
        #    password=Config.password
        #)
        if not login:
            self.wrapper.auth_session(
                session=self.config.session
            )

    def start(self):
        while 1:
            self.config = Config()
            # getting initial start cash
            StatusGrabber(session=self.wrapper)
            start_cap = BankAction(session=self.wrapper).banked
            time.sleep(self.config.sleep_between_actions)
            if self.config.action_enabled(action="bad_santa"):
                Holiday().run(session=self.wrapper)
            mud = Murdering(session=self.wrapper)
            bullet_batch = self.config.bullet_small_batch
            if start_cap > self.config.bullet_medium_batch_cash:
                bullet_batch = self.config.bullet_medium_batch
            if start_cap > self.config.bullet_large_batch_cash:
                bullet_batch = self.config.bullet_large_batch
            # buy bullets
            if start_cap > 2000000:
                mud.do_bullit_action(
                    max_batch=bullet_batch,
                    min_bullets=self.config.min_bullets
                )
                time.sleep(self.config.sleep_between_actions)
                if random.randint(0, 25) == 5:
                    logging.info("Random action hit, opening koffers")
                    mud.do_koffer(max_to_open=15)

            # do gym training
            if self.config.action_enabled(action="gym"):
                mud.do_training()
                time.sleep(self.config.sleep_between_actions)

            # heal if health < 100
            if self.config.action_enabled(action="heal"):
                mud.do_heal()
                time.sleep(self.config.sleep_between_actions)

            # do weapons training
            if self.config.action_enabled(action="weapon_training"):
                mud.do_weapon_training()
                time.sleep(self.config.sleep_between_actions)

            # run trade route once in 10 times
            if self.config.enable_smuggle:
                if self.config.always_do_smuggle:
                    TraderAction().run(session=self.wrapper, runs=2)
                else:
                    if self.config.smuggle_min_cash < start_cap < self.config.smuggle_max_cash:
                        if random.random() > 0.92:
                            logging.info("Trader random hit, running trader for 2 iterations")
                            TraderAction().run(session=self.wrapper, runs=2)
                            time.sleep(self.config.sleep_between_actions)

            # run red-light if enough bullets
            if self.config.enable_pimp:
                if not self.config.pimp_disable_if_bullets_below:
                    PimpAction().run(self.wrapper)
                    time.sleep(self.config.sleep_between_actions)
                else:
                    if mud.bullet_count >= self.config.min_bullets:
                        PimpAction().run(self.wrapper)
                        time.sleep(self.config.sleep_between_actions)

            # run crimes
            if self.config.action_enabled(action="crime"):
                CrimeAction().run(self.wrapper)
                time.sleep(self.config.sleep_between_actions)

            # run carjack
            if self.config.action_enabled(action="car_jack"):
                CarjackAction().run(self.wrapper)
                time.sleep(self.config.sleep_between_actions)

            # get the end amount of cash (for profit per run)
            end_cap = BankAction(session=self.wrapper).banked
            logging.info("Run done earned: %d", (end_cap-start_cap))
            Reporter.report(
                module=self.__class__.__name__,
                action="profit",
                text=str(end_cap-start_cap)
            )
            if end_cap > self.config.trading_min_cash_required:
                if random.random() > 0.5:
                    market = MarketAction(session=self.wrapper)
                    market.max_to_spend = self.config.trading_max_to_offer
                    market.min_buy = self.config.trading_credit_amount
                    market.get_market()
                else:
                    BankAction(session=self.wrapper).donate_familie(
                        amount=50000000
                    )
            if self.config.action_enabled(action="breakout"):
                BreakoutAction().run(session=self.wrapper, count=25, max_runtime=60)
            time.sleep(self.config.sleep_after_run)
        # print(self.wrapper.get_captcha_from_page(get_page.text))


def run(do_login=False, count=0):
    if count > 5:
        return
    b = Bot(login=do_login)
    try:
        b.start()
    except Exception as e:
        logging.error("Got an error: %s", str(e))
        Reporter.report(
            module="bot",
            action="crashed",
            text=str(e)
        )
    time.sleep(10)
    check_login_issues = b.wrapper.action(action="news")
    if "login" in check_login_issues.url:
        logging.info("Session invalidated, logging in again")
        check_config = Config()
        b.wrapper.auth(
            username=check_config.username,
            password=check_config.password
        )
        check_login_issues = b.wrapper.action(action="news")
        if "login" not in check_login_issues.url:
            run(do_login=True, count=count+1)
    else:
        run(do_login=False, count=count+1)


if __name__ == "__main__":
    run()


