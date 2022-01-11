import logging
import random

import requests
import re
import urllib.parse
from cclub_bot.constants import Constants
from cclub_bot.ocr import resolve_stream


class RequestWrapper:

    _session = None
    endpoint = "https://www.crime-club.nl/"
    last_page = "https://www.crime-club.nl/"
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Origin": "https://www.crime-club.nl",
        "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6,af;q=0.5,fr;q=0.4,ru;q=0.3",
        "Cache-Control": "max-age=0"
    }
    last_uuid = None
    last_text = None

    def __init__(self):
        logging.info("Starting session")
        self._session = requests.session()

    def _get_default(self):
        headers = self.default_headers
        headers["Referer"] = self.last_page
        return headers

    def get_page(self, page, params=None):
        action = urllib.parse.urljoin(
            self.endpoint,
            page
        )
        if not params:
            params = {}
        if self.last_uuid:
            params.update({"uid": self.last_uuid})
        response = self._session.get(action, params=params, headers=self._get_default())
        logging.info("GET %s %s %d", action, params, response.status_code)
        if response:
            self.last_text = response.text
            self.last_page = response.url
        return response

    def get_uid_for(self, action):
        get_uid = re.search(r"nav.php\?p=%s&uid=(\w+)" % action, self.last_text)
        if get_uid:
            new_uid = get_uid.group(1)
            if new_uid != self.last_uuid:
                self.last_uuid = new_uid
                logging.debug("Updated uid to %s for action %s", new_uid, action)

    def get_og_captcha(self, captcha_url):
        url = urllib.parse.urljoin(
            self.endpoint,
            captcha_url
        )
        return self._session.get(url, headers=self._get_default()).content

    def post_page(self, page, params=None, data=None):
        action = urllib.parse.urljoin(
            self.endpoint,
            page
        )
        if "reload" in data:
            del data["reload"]
        if not params:
            params = {}
        if self.last_uuid:
            params.update({"uid": self.last_uuid})
        response = self._session.post(
            action, params=params, data=data, headers=self._get_default()
        )
        logging.info("POST %s %s %s %d", action, params, data, response.status_code)
        if response:
            self.last_text = response.text
            self.last_page = response.url
        return response

    def auth(self, username, password):
        self.get_page(Constants.login_page)
        body = {
            "username": username,
            "password": password,
            "submit_login": "Inloggen"
        }
        result = self.post_page(Constants.login_page, data=body)
        if "login.php" in result.url:
            logging.error("Invalid credentials")
            return False
        logging.info("Login for %s successful", username)
        return True

    def auth_session(self, session):
        self._session.cookies.update(
            dict(PHPSESSID=session, regged="yes")
        )
        check = self.action(action="news")
        if "login.php" not in check.url:
            logging.info("Login for session %s successful", session)
            return True
        logging.warning("Session expired, logging in again")
        return False

    def action(self, action, args=None, data=None):
        if not args:
            args = {}
        new_args = {"p": action}
        new_args.update(
            args
        )
        if data:
            result = self.post_page(
                page=Constants.action_page,
                params=new_args,
                data=data
            )
        else:
            result = self.get_page(
                page=Constants.action_page,
                params=new_args
            )
        return result

    def get_captcha_from_page(self, text, has_to_reload=True):
        out = {}
        get_captcha = re.search(
            r'(?s)<img src="(/images/captcha/.+?)".+?<input.+?name="(.+?)"',
            text
        )
        if get_captcha:
            get_captcha_key = get_captcha.group(1)
            get_captcha_form = get_captcha.group(2)
            cracked = self.get_captcha(get_url=get_captcha_key)
            out.update({get_captcha_form: cracked})

        if '$("input[type=\'submit\']").each (function()' in text:
            get_new = re.search(
                'var i = \'<input type="hidden" name="(.+?)".+?value="(.+?)"',
                text
            )
            if get_new:
                out.update({get_new.group(1): get_new.group(2)})

        get_do_crime = self.captcha_do_crime(text)
        if get_do_crime:
            out[get_do_crime] = ""
            if has_to_reload:
                out["reload"] = get_do_crime
        return out

    def captcha_do_crime(self, text):
        get_do_crime = re.search(
            r'/ajax/do_crime.php\?v=(\w+)',
            text
        )
        if ".Captcha()" in text and get_do_crime:
            logging.info("Do-Crime captcha found, submitting")
            rand_pool = list(
                "azertyupqsdfghjkmwxcvbn23456789AZERTYUPQSDFGHJKMWXCVBN_-#@"
            )
            rand_val = "".join([random.choice(rand_pool) for _ in range(32)])
            to_submit = urllib.parse.urljoin(
                self.endpoint,
                f"/ajax/do_crime.php"
            )
            res = self.post_page(
                page=to_submit,
                params={"v": get_do_crime.group(1)},
                data={"action": "captcha", "key": rand_val}
            )
            return rand_val
        return None

    def get_captcha(self, max_captcha_attempt=8, get_url="/images/captcha/captcha.php"):
        for _ in range(max_captcha_attempt):
            get_captcha_content = self.get_og_captcha(captcha_url=get_url)
            cracked = resolve_stream(image=get_captcha_content)
            if cracked:
                return cracked
        return None
