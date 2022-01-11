import logging
import re
import time

import cclub_bot.wrapper
from cclub_bot.actions.bank import BankAction
from cclub_bot.actions.hospital import HospitalAction
from cclub_bot.reporter import Reporter


class Murdering:

    session = False
    bullet_count = None

    def __init__(self, session: cclub_bot.wrapper.RequestWrapper):
        self.session = session

    def do_captcha(self, params={},
                   return_action="weapontraining",
                   return_data={"tab": "weapontraining"}):
        params['captcha_check'] = "check"
        if "reload" in params:
            params[params["reload"]] = ""
        self.session.action(
            action=return_action,
            args=return_data,
            data=params
        )

    def do_heal(self, current_text=None, min_health=100):
        if not current_text:
            self.session.get_uid_for("news")
            get_page = self.session.action(
                action="news"
            )
            current_text = get_page.text
        HospitalAction(session=self.session, last_text=current_text).heal(min_health=min_health)

    def do_koffer(self, max_to_open=30, current_value=0):
        if current_value > max_to_open:
            return False
        self.session.get_uid_for("suitcases")
        get_page = self.session.action(
            action="suitcases"
        )

        get_num = re.search(
            r'Je hebt op het moment <strong>(\d+)</strong> koffer',
            get_page.text
        )

        if not get_num:
            logging.debug("Error reading koffers")
            return False

        koffer_num = int(get_num.group(1))
        if koffer_num == 0:
            logging.debug("No koffers")
            return False

        get_post_action = re.search(
            r"<input type='submit' name='(.+?)' value='Maak een koffer open",
            get_page.text
        )
        if not get_post_action:
            logging.warning("Unable to find koffer action")
            return False

        post = {}
        post.update(
            {get_post_action.group(1): "Maak een koffer open!"}
        )
        get_capt = self.session.get_captcha_from_page(get_page.text)
        if get_capt:
            post.update(get_capt)
        if "captcha_code" in get_capt or "reload" in get_capt:

            self.do_captcha(get_capt, return_action="suitcases")
            logging.info("Submitted captcha, retrying page")
            return self.do_koffer(max_to_open=max_to_open, current_value=current_value)
        do_action = self.session.action(
            action="suitcases",
            data=post
        )
        self.do_heal(
            current_text=do_action.text,
            min_health=40
        )
        logging.info("Opened koffer")
        return self.do_koffer(max_to_open=max_to_open, current_value=current_value+1)

    def do_weapon_upgrade(self, text, step_2=False):
        if step_2:
            post = {
                "mouse_licht": "0"
            }
            post.update(
                {"changeSure": "Ik weet het zeker!"}
            )
            get_capt = self.session.get_captcha_from_page(text, has_to_reload=False)
            if get_capt:
                post.update(get_capt)
            if "code_murdering" in get_capt:
                self.do_captcha(get_capt)
                logging.info("Submitted captcha, retrying page")
                return self.do_weapon_training(retry=True)
            do_action = self.session.action(
                action="murdering",
                args={"tab": "weapontraining"},
                data=post
            )
        else:
            post = {
                "mouse_licht": "0"
            }
            post.update(
                {"change": "Omruilen"}
            )
            get_capt = self.session.get_captcha_from_page(text, has_to_reload=False)
            if get_capt:
                post.update(get_capt)
            if "code_murdering" in get_capt:
                self.do_captcha(get_capt)
                logging.info("Submitted captcha, retrying page")
                return self.do_weapon_training(retry=True)
            do_action = self.session.action(
                action="murdering",
                args={"tab": "weapontraining"},
                data=post
            )
            return self.do_weapon_upgrade(text=do_action.text, step_2=True)

        logging.info("Did weapons upgrade")

    def do_weapon_training(self, retry=False):
        self.session.get_uid_for("murdering&tab=weapontraining")
        get_page = self.session.action(
            action="murdering",
            args={"tab": "weapontraining"}
        )

        if "wachten voordat je weer wapentraining kan doen!" in get_page.text:
            return False

        if '<input type="submit" name="change" value="Omruilen"' in get_page.text:
            logging.info("Upgrading weapon experience")
            self.do_weapon_upgrade(text=get_page.text)
            return True

        get_post_action = re.search(
            r'<input type="submit" name="(.+?)" value="Trainen">',
            get_page.text
        )
        if not get_post_action:
            return False

        post = {
            "mouse_licht": "10"
        }
        post.update(
            {get_post_action.group(1): "Trainen"}
        )
        get_capt = self.session.get_captcha_from_page(get_page.text, has_to_reload=False)
        if get_capt:
            post.update(get_capt)
        if "code_murdering" in get_capt:
            if retry:
                return False
            self.do_captcha(get_capt)
            logging.info("Submitted captcha, retrying page")
            return self.do_weapon_training(retry=True)
        do_action = self.session.action(
            action="murdering",
            args={"tab": "weapontraining"},
            data=post
        )
        logging.info("Did weapons training")
        return True

    def do_training(self, retry=False):
        self.session.get_uid_for("gym")
        get_page = self.session.action(
            action="gym"
        )

        if "Je kunt weer trainen over" in get_page.text:
            logging.debug("Already training, skipping")
            return False

        get_post_action = re.search(
            r'<input type="submit" name="(.+?)" value="Begin training',
            get_page.text
        )
        if not get_post_action:
            logging.warning("Unable to find gym action")
            return False

        post = {
            "training": "1"
        }
        post.update(
            {get_post_action.group(1): "Begin training!"}
        )
        get_capt = self.session.get_captcha_from_page(get_page.text)
        if get_capt:
            post.update(get_capt)
        if "captcha_code" in get_capt or "reload" in get_capt:
            if retry:
                return False
            self.do_captcha(get_capt, return_action="gym", return_data=None)
            logging.info("Submitted captcha, retrying page")
            return self.do_training(retry=True)
        do_action = self.session.action(
            action="gym",
            data=post
        )
        logging.info("Started gym training")
        return True

    def do_bullit_action(self, min_bullets=50000, max_batch=50):
        self.session.get_uid_for("bulletfactory")
        get_page = self.session.action(
            action="bulletfactory"
        )

        if "prison" in get_page.url:
            logging.warning("In prison, trying again in 5 seconds")
            time.sleep(5)
            return self.do_bullit_action(min_bullets, max_batch)

        current_region_data = re.search(
            r'(?s)<tr style="font-weight: bold; color: cadetblue;">(.+?)</tr>',
            get_page.text
        )

        group_data = [x.strip() for x in re.findall('(?s)<td class=\'inhoud\'>(.+?)</td', current_region_data.group(1))]

        get_storage_data = re.search(
            r'(?s)Kogelopslag</td>(.+?)</table>',
            get_page.text
        )
        if not get_storage_data:
            return False
        current_bullets = re.search(
            r'(?s)Jouw kogels</td>.+?>([\d+,]+)<',
            get_storage_data.group(1)
        )
        current_bullet_count = int(current_bullets.group(1).replace(",", ""))
        self.bullet_count = current_bullet_count
        if current_bullet_count + max_batch > min_bullets:
            max_batch = min_bullets - current_bullet_count
        if current_bullet_count < min_bullets:
            get_bullet_price = int(re.sub(r"[^0-9]", "", group_data[2]))
            get_money = max_batch * get_bullet_price
            if not BankAction(session=self.session).withdraw_amount(amount=get_money):
                return False
            logging.info("Buying %s bullets for %s", max_batch, get_money)
            self.session.action(
                action="bulletfactory",
                data={"kogels": max_batch, "koop": "Koop!"}
            )
            Reporter.report(
                module=self.__class__.__name__,
                action="bullets",
                text=f"{max_batch}"
            )
            return True
        return False
