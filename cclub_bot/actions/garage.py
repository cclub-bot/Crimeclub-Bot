import re
import cclub_bot.wrapper
from cclub_bot.reporter import Reporter


class GarageAction:

    session = False
    owned = 0

    def __init__(self, session: cclub_bot.wrapper.RequestWrapper):
        self.session = session
        self.get_garage()

    def get_garage(self):
        self.session.get_uid_for(action="garage")

        overview = self.session.action(
            action="garage"
        )
        self.owned = overview.text.count("Prijs:")

    def sell_all(self, min_amount=0):
        if not self.owned or self.owned < min_amount:
            return False
        self.session.action(
            action="garage",
            data={
                "sellall": "1",
                "min_crush_amount": "0"
            }
        )
        Reporter.report(
            module=self.__class__.__name__,
            action="sell",
            text=str(self.owned)
        )
        return True

