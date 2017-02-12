# DriveAuthBot
A Reddit bot that authorized contributors to a subreddit based on a Google Form response spreadsheet and a score calculated from their responses

## Requirements

* Python 3
* PRAW
* google-api-python-client
* A reddit bot with moderator access
* A Google Sheet of Form responses with columns for:
 * Reddit username of entrant
 * a "score" calculated based off of their response

## Usage

Download the script (into it's own folder), then start it. The initial startup of the bot will walk you through getting the authentication keys and other data necessary for the bot's operation. After the initial boot, the bot will load all it's necessary credentials from `credentials.ini` and `googleAuth.json`.

The bot will refresh at an interval you define. Each refresh, it will download the response spreadsheet and parse it. It will go through the list of redditors; if the redditor has been previously approved or if that attempt to gain access has been recorded, they are ignored. If the user has not been approved, the bot will compare their score to the score you designate during the initial credential aquisition. If the score is greater than or equal to the limit you define, they will be accepted as a contributor, notified via PM, and given the flair of "Noob" (which the moderators can remove when necesary). If they fail, the bot will notify them of the failure. A record of acceptance/failure is kept locally in `archive.list`.
