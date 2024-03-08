class Player:
    def __init__(self, profile_id = "", nickname = "", last_match_ID = ""):
        self.profile_id = profile_id
        self.nickname = nickname
        self.last_match_ID = last_match_ID
        self.stats = {}

    def to_dict(self):
        output = {}
        output["profile_id"] = self.profile_id
        output["nickname"] = self.nickname
        output["last_match_ID"] = self.last_match_ID
        return output

    def load_dict(self, d):
        self.profile_id = d["profile_id"]
        self.nickname = d["nickname"]
        self.last_match_ID = d["last_match_ID"]