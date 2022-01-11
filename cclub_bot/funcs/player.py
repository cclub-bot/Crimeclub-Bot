class Player:
    player_objects = {
        "rank": None,
        "cash": 0,
        "bank": 0,
        "city": None,
        "street": None,
        "clan": None
    }

    attrs = {}

    def set_attr(self, action, key, value):
        if action not in self.attrs:
            self.attrs[action] = {}
        self.attrs[action][key] = value

    def get_attr(self, action, key, default=None):
        if action not in self.attrs:
            return default
        if key not in self.attrs[action]:
            return default
        return self.attrs[action][key]

    @property
    def rank(self):
        return self.player_objects.get(
            "rank"
        )

    @property
    def cash(self):
        return self.player_objects.get(
            "cash"
        )

    @property
    def bank(self):
        return self.player_objects.get(
            "bank"
        )

    @property
    def city(self):
        return self.player_objects.get(
            "city"
        )

    @property
    def street(self):
        return self.player_objects.get(
            "street"
        )

    @property
    def clan(self):
        return self.player_objects.get(
            "clan"
        )
