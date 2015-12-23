import json

def parseConfig(filename):
    with open(filename) as data_file:
        config = json.load(data_file)
        print config

if __name__ == "__main__":
    parseConfig(".config")
