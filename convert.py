from collections import defaultdict
import json
import csv
from urllib.request import urlopen
import os

def rowToDict(header, csvRow):
    goal = dict()
    goal["name"] = csvRow[0]
    goal["jp"] = csvRow[1]
    difficulty = csvRow[2]
    goal["child"] = csvRow[3]

    types = dict()
    subtypes = dict()
    for index, synergy in enumerate(csvRow[4:]):
        if synergy != "":
            typeName = header[index]
            # a '*' denotes a subtype
            if synergy.startswith("*"):
                subtypes[typeName] = float(synergy[1:])
            else:
                types[typeName] = float(synergy)

    # all goals have types
    goal["types"] = types
    # only include the subtypes dict if we have subtypes
    if subtypes:
        goal["subtypes"] = subtypes

    return difficulty, goal


def rowsListToDict(headerRow, goalRows):
    header = headerRow[4:]

    goals = defaultdict(list)
    goals["info"] = {"version": "v9"}

    for row in goalRows:
        try:
            if row[0]:
                difficulty, goal = rowToDict(header, row)
                goals[difficulty].append(goal)
        except:
            print("exception encountered when processing row: " + str(row))

    return goals

def csvToJson(csvFilename, jsonFilename):
    reader = csv.reader(open(csvFilename))
    headerRow = next(reader)
    goalRows = list(reader)

    jsonDict = rowsListToDict(headerRow, goalRows)

    json.dump(jsonDict, open(jsonFilename, "w"), sort_keys = True, indent = 4)



def dictToRow(difficulty, goal, typesList):
    def getSynergy(goal, typeName):
        if typeName in goal["types"]:
            return str(goal["types"][typeName])
        elif "subtypes" in goal and typeName in goal["subtypes"]:
            return "*" + str(goal["subtypes"][typeName])
        else:
            return ""

    info = [goal["name"], goal["jp"], difficulty, goal["child"]]
    types = [getSynergy(goal, typeName) for typeName in typesList]
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

def dictToRowsList(goals):
    typesSet = set()
    for key in goals:
        if key.isdigit():
            for goal in goals[key]:
                typesSet.update(goal["types"].keys())

    typesList = HEADER_ORDER

    header = ["name", "jp", "difficulty", "child"] + typesList

    goalRows = []

    for key in goals:
        if key.isdigit():
            difficulty = key
            for goal in goals[key]:
                goalRows.append(dictToRow(difficulty, goal, typesList))

    return [header] + goalRows


def jsonToCsv(jsonFilename, csvFilename):
    jsonDict = json.load(open(jsonFilename))
    writer = csv.writer(open(csvFilename, "w"))

    rows = dictToRowsList(jsonDict)
    for row in rows:
        writer.writerow(row)


# change this to True if you always want to redownload the csv
ALWAYS_DOWNLOAD = False

BASE_URL = "https://docs.google.com/spreadsheet/ccc"
DOWNLOAD_URL = BASE_URL + "?key=1dRpwfIV2vDRL_Hq-pBj3U7wq7XwZ9JPW9Ac8hK5qbgc&output=csv"

CSV_FILENAME = "goals.csv"
JSON_FILENAME = "goal-list.json"

if __name__ == "__main__":
    try:
        # load the csv if it's not present
        if not os.path.exists(CSV_FILENAME) or ALWAYS_DOWNLOAD:
            print("loading goals csv from google docs")
            data = urlopen(DOWNLOAD_URL).read().decode('utf-8')
            with open(CSV_FILENAME, "w") as goalsCsv:
                goalsCsv.write(data)
            print("goals csv loaded and saved to \"" + CSV_FILENAME + "\"")
        else:
            print("using existing \"" + CSV_FILENAME + "\"")

        # convert the csv to json
        print("converting \"" + CSV_FILENAME + "\" to \"" + JSON_FILENAME + "\"")
        csvToJson(CSV_FILENAME, JSON_FILENAME)
    except Exception as e:
        print("oops, looks like there was an error:")
        traceback.print_exc()
        print("depending on what happened, the output files may be corrupted")
    finally:
        input("press enter to close...")

            


