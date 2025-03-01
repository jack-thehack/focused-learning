# focused-learning
Small python script that scrapes a LinkedIn Learning course for lessons and adds them as individual OmniFocus tasks within a dedicated Project  

Tested on a macOS 15.3.1 system.

Shell script must be made executable.  It then checks for required software and dependencies, installs them if necessary, then runs the python script.

The Python script opens LinkedIn Learning using Selenium.  The end user needs to log in using their own credentials before alerting the terminal window that you're logged in.  Then input the url you wish to scrape into Terminal.  Again in Terminal, enter the name of the new OmniFocus project you want all the lessons in.  The lessons are then added, sequentually numbered.  And the duration for each lesson video is added to the Estimated Duration field within OmniFocus.  It then asks for another URL, if there are more courses you wish to add.

Credentials are held within Selenium in case you want to restart the script any time soon, and don't want to have to log in each time.


