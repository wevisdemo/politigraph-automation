# Politigraph-Automation

[WIP] Repository for automation process as a part of [Politigraph](https://github.com/wevisdemo/politigraph) project
Repository of python code for Politigraph automation process

## Automate VoteEvents and Votes

The system get voteEvents data by scraping [msbis website]().<br>
The website provide the informations of
- Issues that got voted in each day of meeting
- The date of the meeting
- Relavant documents

After we scrape the information of voteEvents, we then proceed to download all of the vote log documents in pdf format, then construct a json data to consist of voteEvent data included id of each voteEvents to parse to OCR process.
