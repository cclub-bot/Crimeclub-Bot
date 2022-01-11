import re
import time

from cclub_bot.wrapper import RequestWrapper


class StatusManager:
    status_map = {
        "weapons_training": "cdwapenervaring"
    }

    result_map = {

    }

    def __init__(self):
        for get_item in self.status_map:
            self.result_map[get_item] = int(time.time())

    def run(self, session: RequestWrapper):
        result = session.action(
            action="status"
        )
        for map_item in self.status_map:
            check_item = re.search(
                r"<span id='%s'>(\d+)<" % map_item,
                result
            )
            if check_item:
                self.result_map[map_item] = int(time.time())+int(check_item.group(1))

