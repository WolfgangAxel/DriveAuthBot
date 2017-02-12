#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  DriveAuthBot.py
#  
#  Copyright 2017 Keaton Brown <linux.keaton@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

def loadCreds(myPath):
    """
    loads the config file, if anything is empty, cause panic
    """
    config = configparser.RawConfigParser()
    config.optionxform = lambda option: option
    config.read(myPath+"credentials.ini")
    if not config.sections():
        raise Exception
    for item in config.sections():
        if not [thing[1] for thing in config[item].items()]:
            raise Exception
    return config

def makeCreds(myPath):
    print("Either this is the first time this script is being run, or there "
          "was an error reading the config file. You will now be walked "
          "through obtaining all the credentials this bot needs in order "
          "to function.")
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    input("We will start with Reddit.\nPress enter to continue... ")
    ############################################################# Reddit
    print(" 1) Go to https://www.reddit.com/prefs/apps and sign in with your "
          "bot account. The bot must have moderator privileges.\n"
          " 2) Press the 'create app' button, then enter the following :\n\n"
          "    Name: DriveAuthBot (or another name if you so wish)\n"
          "    App type: script\n"
          "    description: (leave this blank or enter whatever you wish)\n"
          "    about url: https://github.com/WolfgangAxel/DriveAuthBot\n"
          "    redirect url: http://127.0.0.1:65010/authorize_callback\n\n"
          " 3) Finally, press the 'create app' button.")
    input("Press enter to continue... ")
    print("Underneath the name of the app, there should be a string of letters and numbers.\n"
          "That is the bot's client-id.\n"
          "The bot's secret is displayed in the table.")
    redCreds = {}
    for short,thing in [["u","username"],["p","password"],["c","client-id"],["s","secret"]]:
        while True:
            value = input("Please enter the bot's "+thing+":\n==> ")
            confirm = input("Is '"+value+"' correct? (y/n)\n==> ")
            if confirm.lower() == "y":
                redCreds[short] = value
                break
            print("Confirmation failed. Restarting entry")
    input("Reddit credentials done. Starting Google credentials.\nPress enter to continue... ")
    ############################################################# Google
    print("1) Go to https://console.developers.google.com/start/api?id=drive and sign in.\n"
          "2) Press 'Continue', then 'Go to credentials'.\n"
          "3) Press 'Cancel' at the bottom of the 'Add credentials' page.\n"
          "4) Go to the 'OAuth concent screen' tab, enter 'DriveAuthBot' (or whatever) as the name, and press 'Save'.\n"
          "5) Go to the 'Credentials' tab, then press 'Create credentials', and select OAuth client ID.\n"
          "6) Select 'Other', then enter 'DriveAuthBot' (or whatever) as a name.\n"
          "7) Press 'Okay', then to the right, press the 'Download JSON' button\n"
          "8) Move the .json file into "+myPath+" and rename it to 'client_secret.json'")
    input("When you have completed all of the above, press enter to have the script load your credentials.")
    while True:
        try:
            credentials = getGoogleCreds()
            break
        except Exception as e:
            input("Error while creating credentials:\n"+str(e.args)+"\nEnsure all the steps above were followed and press enter to try again...")
    gglCreds = {}
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("drive","v3",http=http)
    results = service.files().list().execute()
    items = results.get('files', [])
    print("Please select the spreadsheet of the signup form:")
    spreadsheets = [spreadsheet for spreadsheet in items if spreadsheet['mimeType'] == 'application/vnd.google-apps.spreadsheet']
    for i,sheet in enumerate(spreadsheets):
        print("  ["+str(i)+"] "+sheet['name'])
    while True:
        i = input("(0-"+str(len(spreadsheets)-1)+"): ")
        try:
            form = spreadsheets[eval(i)]
            confirm = input("Use "+form['name']+"?\n(y/n): ")
            if confirm == "y":
                break
            else:
                print("Confirmation failed. Try again.")
        except:
            print("Failed to pick a sheet. Try again")
    gglCreds['fileID'] = form['id']
    responses = service.files().export(fileId=gglCreds["fileID"],mimeType='text/csv').execute()
    parsed = parseSpreadsheet(responses)
    headers = [title for title in parsed]
    for variable, thing in [["redCol","redditor usernames column"],
                            ["scrCol","score column"],
                            ["timCol","timestamp column"]]:
        print("Please select the "+thing+":")
        for i,title in enumerate(headers):
            print("  ["+str(i)+"] "+title)
        while True:
            i = input("(0-"+str(len(headers)-1)+"): ")
            try:
                confirm = input("Use '"+headers[eval(i)]+"'?\n(y/n): ")
                if confirm == "y":
                    gglCreds[variable] = headers[eval(i)]
                    break
                else:
                    print("Confirmation failed. Try again.")
            except:
                print("Failed to pick a "+thing+". Try again")
    
    input("Almost done! Just a few more items to define.\nPress enter to continue... ")
    ############################################################### Misc
    mscCreds = {}
    for variable,question in [ ["mySub","Enter the name of your subreddit."],
                               ["botMaster","Enter your personal Reddit username. (This is used for Reddit's user-agent, nothing more)"],
                               ["scoreLim","Enter the minimum score the user has to get in order to gain access to the sub."],
                               ["sleepTime","How many seconds to wait between refreshing? (Use whole numbers like 300 or expressions like 5 * 60)"]
                             ]:
        while True:
            value = input(question+"\n==>")
            confirm = input("Is '"+value+"' correct? (y/n)\n==> ")
            if confirm.lower() == "y":
                mscCreds[variable] = value
                break
            print("Confirmation failed. Restarting entry.")
    
    config["R"] = redCreds
    config["G"] = gglCreds
    config["M"] = mscCreds
    with open(myPath+"credentials.ini","w") as cfg:
        config.write(cfg)
    print("Config file written successfully")
    return config

def getGoogleCreds():
    """
    Get credentials from file on local disk
    """
    store = Storage(myPath+"googleAuth.json")
    credentials = store.get()
    if not credentials or credentials.invalid:
        SCOPES = 'https://www.googleapis.com/auth/drive'
        flow = client.flow_from_clientsecrets(myPath+"client_secret.json", SCOPES)
        flow.user_agent = "DriveAuthBot"
        input("Press enter to open the default web browser to grant the script permission to your Google account")
        credentials = tools.run_flow(flow, store)
    return credentials

def parseSpreadsheet(responses):
    """
    Breaks a google sheet into a dictionary with the first row values as keys
    """
    parsed = {}
    reader = csv.reader(str(responses,"utf-8").splitlines())
    header = reader.__next__()
    # Make each column header a dictionary entry
    for name in header:
        parsed[name] = []
    # Put the cells in the appropriate dictionary entry
    for row in reader:
        for i, value in enumerate(row):
            parsed[header[i]].append(value)
    return parsed

########################################################################
#                                                                      #
#    Script Startup                                                    #
#                                                                      #
########################################################################

myPath = __file__.replace("DriveAuthBot.py","")

try:
    mod = "praw"
    import praw
    mod = "configparser"
    import configparser
    mod = "time"
    import time
    mod = "httplib2"
    import httplib2
    mod = "csv"
    import csv
    # google-api-python-client provides the next few imports
    mod = "google-api-python-client"
    import googleapiclient
    del googleapiclient
    from apiclient import discovery
    from oauth2client import client
    from oauth2client import tools
    from oauth2client.file import Storage
except:
    exit(mod+" was not found. Install "+mod+" with pip to continue.")

# Open the archive saved on disk
try:
    with open(myPath+"archive.list","r") as f:
        archive = eval(f.read())
except:
    # Make emptyy archive if archive is missing
    archive = {}
    archive['approved'] = []
    archive['denied'] = []

# Try to load credentials from file, walk user through them if not found
try:
    creds = loadCreds(myPath)
except:
    creds = makeCreds(myPath)

# explicitly define variables found on file
for variable in creds["M"]:
    exec(variable+' = creds["M"]["'+variable+'"]')
sleepTime = eval(sleepTime)
scoreLim = eval(scoreLim)

## Google authentication
credentials = getGoogleCreds()
http = credentials.authorize(httplib2.Http())
service = discovery.build("drive","v3",http=http)
print("Google authentication success!")

## Reddit authentication
R = praw.Reddit(client_id = creds["R"]["c"],
                client_secret = creds["R"]["s"],
                password = creds["R"]["p"],
                user_agent = "DriveAuthBot, a bot for /r/"+mySub.replace("/r/","").replace("r/","")+"; hosted by /u/"+botMaster.replace("/u/","").replace("u/",""),
                username = creds["R"]["u"].replace("/u/","").replace("u/",""))
print("Reddit authentication success!")

print("Bot successfully loaded. Entering main loop.")
sub = R.subreddit(mySub.replace("/r/","").replace("r/",""))
while True:
    try:
        # Download the spreadsheet
        responses = service.files().export(fileId=creds["G"]["fileID"],mimeType='text/csv').execute()
        # Parse it.
        parsed = parseSpreadsheet(responses)
        for i,redditor in enumerate(parsed[creds["G"]["redCol"]]):
            # Standardize username
            redditor = redditor.replace("/u/","").replace("u/","").lower()
            if redditor in archive['approved'] or parsed[creds["G"]["timCol"]][i]+redditor in archive['denied']:
                continue
            print("New redditor found: "+redditor)
            score = eval(parsed[creds["G"]["scrCol"]][i])
            if score >= scoreLim:
                # Congratulations!
                sub.contributor.add(redditor)
                sub.flair.set(redditor,"Noob")
                archive['approved'].append(redditor)
                R.redditor(redditor).message("Approval success","You scored high enough to earn acces to post in /r/"+mySub.replace("/r/","").replace("r/",""))
                with open(myPath+"archive.list","w") as f:
                    f.write(str(archive))
            else:
                R.redditor(redditor).message("Approval failure","You did not score high enough to earn acces to post in /r/"+mySub.replace("/r/","").replace("r/",""))
                archive['denied'].append(parsed[creds["G"]["timCol"]][i]+redditor)
                with open(myPath+"archive.list","w") as f:
                    f.write(str(archive))
        time.sleep(sleepTime)
    except Exception as e:
        print("Error during main loop. Details:\n"+str(e.args)+"\nWill try again in one minute.")
        time.sleep(60)
