#Script required
- python 

#Setup Windows Task Schdule
- set up General > checked "Run whether user is logged on or not" > checked "Run with highest privileges"
- set New Trigger > Begin the task:  On an Event, Log: Microsoft - Windows - NetworkProfile/Operational, Source: NetworkProfile, Event ID:10000
- set New Actions > Action: Start a program, Program/script: path to python.exe (pythonw.exe if need to run in background) , Add arguments (options): path to script agent.py, Start in (options): path to folder agent.py
- set Conditions > Power: unchecked Start the task only if ...

#How to use
- place script agent.py in some path whatever you want.
- set Task Schdule to call script agent.py when connect to new wifi profile 
