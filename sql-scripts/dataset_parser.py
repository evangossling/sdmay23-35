import os
import json
import sys
from alive_progress import alive_bar
import mysql.connector
import datetime

# Set up connection to SQL database
mydb = mysql.connector.connect(
    host="HOST",
    user="USER",
    password="PASSWORD",
    database="DB_NAME",
    charset='utf8mb4',
    use_unicode=True
)
c = mydb.cursor()
progress = ""
completed = []
failed = []
baseDir = ""

# configs
runMode = "failed"  # failed, normal, single
runDevice = "server"  # server, mac, windows

# Set baseDir
if runDevice == "server":
    baseDir = "/home/vm-user/aps-data/"
if runDevice == "mac":
    baseDir = "/Users/pbrink21/Code/aps-dataset/"
if runDevice == "windows":
    baseDir = "C:/Users/pbrin/Downloads/aps-dataset-metadata-2021/"

# generate proper dirs
allFilesDir = baseDir + "aps-dataset-metadata-2021/"
completedFile = baseDir + "completed.txt"
failedFile = baseDir + "failed.txt"
singleFile = allFilesDir + "PRB/99/PhysRevB.99.054407.json"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Function to read JSON file and insert data into database
def process_json_file(filepath):
    with open(filepath, encoding="utf8") as f:
        data = json.load(f)

        # publishers object
        global progress
        progress = "publisher"
        pData = data["publisher"]
        pname = pData["name"]
        c.execute("SELECT * FROM publishers WHERE name = %s", [pname])
        tempData = c.fetchall()
        if c.rowcount == 0:
            c.execute("INSERT INTO publishers (name) VALUES (%s)", [pname])
            mydb.commit()
            publisherID = c.lastrowid
        else:
            publisherID = tempData[0][0]

        # journal object
        progress = "journal"
        jData = data["journal"]
        jID = jData["id"]
        jabbreviatedName = ""
        if "abbreviatedName" in jData:
            jabbreviatedName = jData["abbreviatedName"]
        jname = jData["name"]
        c.execute("SELECT * FROM journals WHERE journalID = %s", [jID])
        tempData = c.fetchall()
        if c.rowcount == 0:
            c.fetchall()
            c.execute("INSERT INTO journals (journalID, abbreviatedName, name) VALUES (%s, %s, %s)",
                      (jID, jabbreviatedName, jname))
            mydb.commit()
            journalID = c.lastrowid
        else:
            journalID = tempData[0][0]

        # paper object
        progress = "paper"
        doi = data["id"]
        c.execute("SELECT * FROM papers WHERE doi = %s", [doi])
        tempData = c.fetchall()
        if c.rowcount == 0:
            title = data["title"]
            issue = 0
            if "issue" in data:
                issue = data["issue"]["number"]
            volume = 0
            if "volume" in data:
                volume = data["volume"]["number"]
            pageStart = 0
            if "pageStart" in data:
                pageStart = data["pageStart"]
            hasArticleId = 0
            if "hasArticleId" in data:
                hasArticleId = data["hasArticleId"]
            date = ""
            if "date" in data:
                date = data["date"]
            numpages = 0
            if "numPages" in data:
                numpages = data["numPages"]
            articleType = ""
            if "articleType" in data:
                articleType = data["articleType"]
            rights = ""
            if "rights" in data:
                rights = data["rights"]
            classificationSchemes = ""
            if "classificationSchemes" in data:
                classificationSchemes = data["classificationSchemes"]
            c.execute(
                "INSERT INTO papers (doi, title, title_format, issue, volume, pageStart, hadArticleID, date, numpages, articleType, classificationSchemes, rights, journalID, publisherID) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (doi, title['value'], title['format'], issue, volume, pageStart, hasArticleId, date, numpages,
                 articleType,
                 json.dumps(classificationSchemes), json.dumps(rights), journalID, publisherID))
            mydb.commit()
            paperID = c.lastrowid
        else:
            paperID = tempData[0][0]

        # affiliations
        affiliations = {}
        progress = "affiliations"
        if "affiliations" in data:
            for lData in data["affiliations"]:
                lname = lData["name"]
                lID = lData["id"]
                # TODO: Get lat and lon
                c.execute("SELECT * FROM places WHERE name = %s", [lname])
                tempData = c.fetchall()
                if c.rowcount == 0:
                    c.execute("INSERT INTO places (name) VALUES (%s)", [lname])
                    mydb.commit()
                    pID = c.lastrowid
                else:
                    pID = tempData[0][0]
                affiliations[lID] = pID
                # paper_place join table
                c.execute("SELECT * FROM paper_place WHERE paperID = %s AND placeID = %s", (paperID, pID))
                c.fetchall()
                if c.rowcount == 0:
                    c.execute("INSERT INTO paper_place (paperID, placeID) VALUES (%s, %s)", (paperID, pID))
                    mydb.commit()

        # authors
        progress = "authors"
        if "authors" in data:
            for aData in data["authors"]:
                type = ""
                if "type" in aData:
                    type = aData["type"]
                name = aData["name"]
                firstname = ""
                surname = ""
                if "firstname" in aData:
                    firstname = aData["firstname"]
                if "surname" in aData:
                    surname = aData["surname"]
                aStr = ""
                affs = []
                if "affiliationIds" in aData:
                    for afID in aData["affiliationIds"]:
                        if afID in affiliations:
                            aStr = aStr + str(affiliations[afID]) + ", "
                            affs.append(afID)
                    if len(aStr) > 0:
                        aStr = aStr[:-2]
                        c.execute("SELECT * FROM authors JOIN author_place ON author_place.authorID=authors.id "
                                  "WHERE authors.name = %s AND author_place.placeID IN (" +
                                  aStr + ");", [name])
                    else:
                        c.execute("SELECT * FROM authors WHERE authors.name = %s", [name])
                tempData = c.fetchall()
                if c.rowcount == 0:
                    c.execute("INSERT INTO authors (name, type, firstname, surname) VALUES (%s, %s, %s, %s)",
                              (name, type, firstname, surname))
                    mydb.commit()
                    aID = c.lastrowid
                else:
                    aID = tempData[0][0]

                # author_place
                for afID in affs:
                    c.execute("SELECT * FROM author_place WHERE authorID = %s AND placeID = %s",
                              (aID, affiliations[afID]))
                    c.fetchall()
                    if c.rowcount == 0:
                        c.execute("INSERT INTO author_place (authorID, placeID) VALUES (%s, %s)",
                                  (aID, affiliations[afID]))
                        mydb.commit()

                # paper_author
                c.execute("SELECT * FROM paper_author WHERE paperID = %s AND authorID = %s", (paperID, aID))
                c.fetchall()
                if c.rowcount == 0:
                    c.execute("INSERT INTO paper_author (paperID, authorID) VALUES (%s, %s)", (paperID, aID))
                    mydb.commit()

        # add to completed, because it hasn't crashed yet
        f = open(completedFile, 'a')
        f.write(filepath + "\n")
        f.close()


# traverse one specified file
if runMode == "single":
    process_json_file(singleFile)
    sys.exit()

if runMode == "failed":
    file = open(failedFile, 'r')
    failed = file.readlines()
    file.close()
    with alive_bar(len(failed)) as bar:
        for file in failed:
            if file[0] == "/" and file not in completed:  # won't work on windows
                process_json_file(file.rstrip())
                bar()
            else:
                bar(skipped=True)
    sys.exit()

# find totals and stuff, for progress bar
totalFiles = 0
for root, dirs, files in os.walk(allFilesDir):
    totalFiles += len(files)

# grab the list of completed files
file = open(completedFile, 'r')
completed = file.readlines()
file.close()

# add a marker to the failed file
f = open(failedFile, 'a')
now = datetime.datetime.now().strftime("%B %d, %Y")
f.write("\n=========== Files failed for script started at " + now + " ===========\n")
f.close()

# Traverse directory and process JSON files
i = 0
with alive_bar(totalFiles) as bar:
    for root, dirs, files in os.walk(allFilesDir):
        for file in files:
            if file.endswith(".json"):
                filepath = os.path.join(root, file)
                if filepath + "\n" in completed:
                    # print(bcolors.WARNING + "already did: " + bcolors.ENDC + filepath)
                    bar(skipped=True)
                else:
                    try:
                        # print(bcolors.BOLD + "running on: " + bcolors.ENDC + filepath)
                        process_json_file(filepath)
                        bar()
                    except Exception as e:
                        print(bcolors.FAIL + "failed " + bcolors.ENDC + "at " + progress + " on: " + filepath)
                        print(e)
                        failed.append(filepath)
                        bar(skipped=True)
                        # add to failed
                        f = open(failedFile, 'a')
                        f.write(filepath + "\n")
                        f.close()

                        # sys.exit()
print("i failed these papers: ")
print(failed)

# Close connection to SQL database
mydb.close()

# rights objects
# rData = data["rights"]
# rightsStatement = rData["rightsStatement"]
# copyrightYear = rData["copyrightYear"]
# creativeCommons = rData["creativeCommons"]
# c.execute("INSERT INTO rights (rightsStatement, copyrightYear, creativeCommons) VALUES (%s, %s, %s)",
#           (rightsStatement, copyrightYear, creativeCommons))
# mydb.commit()
# print(c.rowcount, "right inserted.")
# rightsID = c.lastrowid

# license objects
# licenses = []
# for liData in rData["licenses"]:
#     liType = liData["type"]
#     liURL = liData["url"]
#     usageStatement = liData["usageStatement"]
#     c.execute("SELECT * FROM licenses WHERE url = %s", liURL)
#     if c.rowcount == 0:
#         c.execute("INSERT INTO licenses (type, url, usageStatement, usageStatementFormat) "
#                   "VALUES (%s, %s, %s, %s)",
#                   (liType, liURL, usageStatement['value'], usageStatement['format']))
#         mydb.commit()
#         print(c.rowcount, "licence inserted.")
#         liID = c.lastrowid
#     else:
#         liID = c.fetchone()["id"]
#     # check if the relationship already exists, if not continue to add that as well
#     c.execute("SELECT * FROM right_license WHERE rightID = %s AND licenseID = %s", (rightsID, liID))
#     if c.rowcount == 0:
#         c.execute("INSERT INTO right_license (rightID, licenseID) VALUES (%s, %s)", (rightsID, liID))
#         mydb.commit()
#         print(c.rowcount, "right_license inserted.")

# mac file dirs
# dir = "/Users/pbrink21/Code/aps-dataset/aps-dataset-metadata-2021/"
# completedFileDir = "/Users/pbrink21/Code/aps-dataset/completed.txt"
# failedFile = "/Users/pbrink21/Code/aps-dataset/failed.txt"
# singleFile = "/Users/pbrink21/Code/aps-dataset/aps-dataset-metadata-2021/PRB/99/PhysRevB.99.054407.json"

# windows file dirs
# dir = "C:/Users/pbrin/Downloads/aps-dataset-metadata-2021/aps-dataset-metadata-2021/"
# completedFileDir = "C:/Users/pbrin/Downloads/aps-dataset-metadata-2021/completed.txt"
# failedFile = "C:/Users/pbrin/Downloads/aps-dataset-metadata-2021/failed.txt"
# singleFile = "/Users/pbrink21/Code/aps-dataset/aps-dataset-metadata-2021/PRB/99/PhysRevB.99.054407.json"

# server file dirs
# dir = "/home/vm-user/aps-data/aps-dataset-metadata-2021/"
# completedFileDir = "/home/vm-user/aps-data/completed.txt"
# failedFile = "/home/vm-user/aps-data/failed.txt"
# singleFile = "/Users/pbrink21/Code/aps-dataset/aps-dataset-metadata-2021/PRB/99/PhysRevB.99.054407.json"
