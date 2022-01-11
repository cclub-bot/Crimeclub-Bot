import logging
import re
import time

from cclub_bot.actions.actions import BaseAction
from cclub_bot.actions.bank import BankAction
from cclub_bot.actions.garage import GarageAction
from cclub_bot.reporter import Reporter
from cclub_bot.wrapper import RequestWrapper


class PimpAction(BaseAction):
    action = "redlightdistrict"

    def __init__(self):
        super(PimpAction, self).__init__()

    def run(self, session: RequestWrapper):
        session.get_uid_for(self.action)
        result = session.action(
            action=self.action
        )
        post = {}
        get_capt = session.get_captcha_from_page(result.text)
        if get_capt:
            post.update(get_capt)
        if "code_redlightdistrict" in get_capt or "reload" in get_capt:
            self.do_captcha(get_capt, session=session)
            logging.info("Submitted captcha, retrying page")
            return self.run(session=session)
        get_post_action = re.search(
            r"<input type='submit' name='(.+?)' value='Pimpen'",
            result.text
        )
        if not get_post_action:
            return None
        post.update({
            "mouse_licht": "2"
        })
        post.update(
            {get_post_action.group(1): "Pimpen"}
        )
        do_action = session.action(
            action=self.action,
            data=post
        )

        result = session.action(
            action=self.action
        )

        get_available = re.search(r'text\.value\s*=\s*"(\d+)"', result.text)
        if get_available and get_available.group(1) != "0":
            Reporter.report(
                module=self.__class__.__name__,
                action="pimped",
                text=get_available.group(1)
            )
            post = {
                "numRamen": get_available.group(1),
                "hire": "Huren"
            }
            get_capt = session.get_captcha_from_page(result.text)
            if get_capt:
                post.update(get_capt)
            if "captcha_code" in get_capt or "reload" in get_capt:
                self.do_captcha(get_capt, session=session)
                logging.info("Submitted captcha, retrying page")
                return self.run(session=session)

            session.action(
                action="redlightdistrict",
                data=post
            )
            Reporter.report(
                module=self.__class__.__name__,
                action="windowed",
                text=get_available.group(1)
            )

        return True


class Holiday(BaseAction):
    action = "holiday"

    def __init__(self):
        super(Holiday, self).__init__()

    def run(self, session: RequestWrapper):
        session.get_uid_for(self.action)
        result = session.action(
            action=self.action
        )
        if "Hij komt weer terug over" in result.text:
            return
        post = {"attack": "Aanvallen!"}
        result = session.action(
            action=self.action,
            data=post
        )
