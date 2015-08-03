from collections import defaultdict
import json
import csv
from urllib.request import urlopen
import os
import traceback


class ValueColumn:

    def __init__(self, name):
        self.name = name

    @property
    def included(self):
        return True

class StringColumn(ValueColumn):

    def parse_value(self, value):
        return value

class IntegerColumn(ValueColumn):

    def parse_value(self, value):
        return int(value)

class Ignore:

    def __init__(self, name):
        self.name = name

    @property
    def included(self):
        return False

SCHEMA = [
    StringColumn("name"),
    StringColumn("jp"),
    StringColumn("difficulty"),
    StringColumn("child")
]

def parse_goal(col_details):
    return {col.name: col.parse_value(detail) for col, detail in col_details}

def row_to_dict(synergy_header, row):
    detail_cols = row[:len(SCHEMA)]
    synergy_cols = row[len(SCHEMA):]

    goal = parse_goal([(col, detail) for col, detail in zip(SCHEMA, detail_cols) if col.included])

    types = dict()
    subtypes = dict()
    for synergy_name, synergy in zip(synergy_header, synergy_cols):
        if synergy:
            if synergy.startswith("*"):
                subtypes[synergy_name] = float(synergy[1:])
            else:
                types[synergy_name] = float(synergy)

    # all goals have types
    goal["types"] = types
    # only include the subtypes dict if we have subtypes
    if subtypes:
        goal["subtypes"] = subtypes

    return goal


def rows_to_dict(header, rows):
    synergy_header = header[len(SCHEMA):]

    goals = defaultdict(list)
    goals["info"] = {"version": "v9"}

    for row in rows:
        try:
            if row[0]:
                goal = row_to_dict(synergy_header, row)
                difficulty = goal.pop("difficulty")
                goals[difficulty].append(goal)
        except Exception as e:
            print("Exception occured when processing row:", row)
            raise e

    return goals

def csv_to_json(csv_filename, json_filename):
    reader = csv.reader(open(csv_filename, encoding="utf-8"))
    header = next(reader)
    rows = list(reader)

    json_dict = rows_to_dict(header, rows)
    json_str = json.dumps(json_dict, sort_keys = True, indent = 4)

    output = "var bingoList = " + json_str
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json_file.write(output)


def dict_to_row(difficulty, goal, types):
    def get_synergy(goal, type_name):
        if type_name in goal["types"]:
            return str(goal["types"][type_name])
        elif "subtypes" in goal and type_name in goal["subtypes"]:
            return "*" + str(goal["subtypes"][type_name])
        else:
            return ""

    info = [goal["name"], goal["jp"], difficulty, goal["child"]]
    types = [get_synergy(goal, type_name) for type_name in types]
    return info + types

# this is the order that gombill specified
# eventually we should try to preserve the order in the file
HEADER_ORDER = ['childzl', 'saria', 'zl', 'lightarrow', 'claimcheck', 'magic',
                'forest', 'quiver', 'pg', 'gtunic', 'dmc', 'fire', 'ice',
                'irons', 'water', 'longshot', 'hovers', 'shadow', 'fortress',
                'gerudo', 'gtg', 'spirit', 'deku', 'ganon', 'dc', 'kd', 'jabu',
                'lonlon', 'childchu', 'beans', 'songs', 'swords', 'botw', 'child2',
                'mapcompass', 'hearts', 'wallet', 'strength', 'bottle', 'bulletbag',
                'bombbag', 'nuts', 'shields', 'cow', 'skullkid', 'atrade', 'boots', 'tunics']

def dict_to_rows(goals):
    types = set()
    for key in goals:
        if key.isdigit():
            for goal in goals[key]:
                types.update(goal["types"].keys())

    types = HEADER_ORDER

    header = ["name", "jp", "difficulty", "child"] + types

    rows = []

    for key in goals:
        if key.isdigit():
            difficulty = key
            for goal in goals[key]:
                rows.append(dict_to_row(difficulty, goal, types))

    return [header] + rows


def json_to_csv(json_filename, csv_filename):
    json_dict = json.load(open(json_filename, encoding="utf-8"))
    writer = csv.writer(open(csv_filename, "w", encoding="utf-8"))

    rows = dict_to_rows(json_dict)
    for row in rows:
        writer.writerow(row)


# set this to True if you always want to redownload the csv
# set this to False if you want it to use the "goals.csv" file
ALWAYS_DOWNLOAD = True

BASE_URL = "https://docs.google.com/spreadsheet/ccc"
DOWNLOAD_URL = BASE_URL + "?key=1dRpwfIV2vDRL_Hq-pBj3U7wq7XwZ9JPW9Ac8hK5qbgc&output=csv"

CSV_FILENAME = "goals.csv"
JSON_FILENAME = "goal-list.js"

if __name__ == "__main__":
    try:
        # load the csv if it's not present
        if not os.path.exists(CSV_FILENAME) or ALWAYS_DOWNLOAD:
            print("loading goals csv from google docs")
            data = urlopen(DOWNLOAD_URL).read().decode('utf-8')
            with open(CSV_FILENAME, "w", encoding="utf-8") as goals_csv:
                goals_csv.write(data)
            print("goals csv loaded and saved to \"" + CSV_FILENAME + "\"")
        else:
            print("using existing \"" + CSV_FILENAME + "\"")

        # convert the csv to json
        print("converting \"" + CSV_FILENAME + "\" to \"" + JSON_FILENAME + "\"")
        csv_to_json(CSV_FILENAME, JSON_FILENAME)
    except Exception as e:
        print("oops, looks like there was an error:")
        traceback.print_exc()
        print("depending on what happened, the output files may be corrupted")
    finally:
        input("press enter to close...")




