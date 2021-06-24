import glob
import json
from os import path

basepath = path.abspath(path.dirname(__file__))
talktracks_path = path.join(basepath, 'talktracks', '*.json')


def get_talktrack_file_parsed_contents() -> list[dict]:
    files = glob.iglob(talktracks_path)

    contents = []
    for filename in files:
        with open(filename) as file:
            content = json.load(file)
            contents.append(content)

    return contents
