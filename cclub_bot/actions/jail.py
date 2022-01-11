import logging
import re
import time

from cclub_bot.actions.actions import BaseAction
from cclub_bot.reporter import Reporter
from cclub_bot.wrapper import RequestWrapper
from config2 import Config


class BreakoutAction(BaseAction):
    action = "prison"
    max_count = 50
    max_int = None

    def __init__(self):
        super(BreakoutAction, self).__init__()

    def run(self, session: RequestWrapper, count=0, last_action=None, max_runtime=None):
        if not self.max_int and max_runtime:
            self.max_int = int(time.time()) + max_runtime
        if self.max_int and self.max_int < int(time.time()):
            self.max_int = None
            return
        if count > self.max_count:
            self.max_int = None
            return
        session.get_uid_for(self.action)
        if not last_action:
            result = session.action(
                action=self.action
            )
        else:
            result = last_action
        if f"class='donator'>{Config().username}</a>" in result.text:
            logging.warning("I am jailed, waiting..")
            time.sleep(2)
            return self.run(session, count + 1)

        get_post_action = re.search(
            r"<input type='submit' name='(.+?)' value='Breek uit!'",
            result.text
        )
        if not get_post_action:
            time.sleep(0.765)
            return self.run(session, count+1)
        post = {
            "mousebreak": "0",
            "mousebuyout": "0"
        }
        post.update(
            {get_post_action.group(1): "Breek uit!"}
        )
        get_capt = session.get_captcha_from_page(result.text)
        if get_capt:
            post.update(get_capt)
        if "captcha_code" in get_capt or "reload" in get_capt:
            self.do_captcha(get_capt, session=session)
            logging.info("Submitted captcha, retrying page")
            return self.run(session=session)
        do_action = session.action(
            action=self.action,
            data=post
        )
        if "uit de gevangenis gebroken!" in do_action.text:
            Reporter.report(
                module=self.__class__.__name__,
                action="unjail",
                text="success"
            )
            logging.info("Unjailed successfully")
        else:
            time.sleep(1.75)
        return self.run(
            session=session,
            count=count+1,
            last_action=do_action
        )
