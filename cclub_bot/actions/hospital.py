import re
import logging
import cclub_bot.wrapper
from cclub_bot.actions.bank import BankAction
from cclub_bot.reporter import Reporter


class HospitalAction:

    session = False
    leven = 0

    def __init__(self, session: cclub_bot.wrapper.RequestWrapper, last_text=None):
        self.session = session
        get_leven = re.search(
            r'(?s)Leven:.+?<span>(\d+)%</span>',
            last_text
        )
        if get_leven:
            self.leven = int(get_leven.group(1))

    def heal(self, min_health=100):
        if self.leven >= min_health:
            return False
        logging.warning("Level below 100 (%s), attempting heal", self.leven)
        self.session.get_uid_for("hospital")
        get_hospital = self.session.action(
            "hospital"
        )

        get_uid = re.search(
            r"(?s)<option value='(\d+)' class='hurtList' selected='selected'.+?\$(.+?)<",
            get_hospital.text
        )
        if not get_uid:
            return False
        post = {
            "hospital": get_uid.group(1),
            "submit_heal": "Maak jezelf levend!"
        }
        get_capt = self.session.get_captcha_from_page(get_hospital.text)
        if get_capt:
            post.update(get_capt)
        BankAction(self.session).withdraw_amount(
            amount=int(re.sub("[^0-9]", "", get_uid.group(2)))
        )
        self.session.action(
            action="hospital",
            data=post
        )
        Reporter.report(
            module=self.__class__.__name__,
            action="heal",
            text=f"{self.leven} -> {min_health}"
        )
        return True


class StatusGrabber:

    session = False

    def __init__(self, session: cclub_bot.wrapper.RequestWrapper, last_text=None):
        self.session = session
        self.grab()

    def grab(self):
        self.session.get_uid_for(action="status")
        status = self.session.action(
            action="status"
        )
        pool = {}
        good_page = status.text.split("<form")[1].split("</form")[0]
        groups = re.findall(
            '(?s)(<tr.+?</tr>)',
            good_page
        )
        for entry in groups:
            if entry.count("</td") == 2:
                td_entries = re.findall(
                    '(?s)(<td.+?</td>)',
                    entry
                )
                entry_key = td_entries[0]
                entry_value = td_entries[1]
                entry_key = re.sub('(?s)<.+?>', "", entry_key).strip()
                entry_value = re.sub('(?s)<.+?>', "", entry_value).strip()
                pool[entry_key] = entry_value
        Reporter.report_pool(pool)
