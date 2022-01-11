class BaseAction:
    action = None
    session = None

    def __init__(self):
        pass

    def do_captcha(self, params={}, session=None):
        params['captcha_check'] = "check"
        if "reload" in params:
            params[params["reload"]] = ""
        session.action(
            action=self.action,
            data=params
        )
