import json

class Config:
    def __init__(self, filename=".config"):
        with open(filename) as data_file:
            self.config = json.load(data_file)

    @property
    def src(self):
        return self.config["src"]

    @property
    def dst(self):
        return self.config["dst"]
    
    @property
    def extn(self):
        return self.config["extn"]

if __name__ == "__main__":
    cfg = Config(".config")
    print cfg.src
    print cfg.extn
    print cfg.dst
