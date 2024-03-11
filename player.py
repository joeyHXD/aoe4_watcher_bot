class Player:
    def __init__(self, profile_id = "", nickname = "", updated_at = ""):
        self.profile_id = profile_id
        self.nickname = nickname
        self.updated_at = updated_at
        self.stats = {}

    def to_dict(self):
        output = {}
        output["profile_id"] = self.profile_id
        output["nickname"] = self.nickname
        output["updated_at"] = self.updated_at
        return output

    def load_dict(self, d):
        self.profile_id = d["profile_id"]
        self.nickname = d["nickname"]
        self.updated_at = d["updated_at"]