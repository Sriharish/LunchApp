# LunchApp Overview
Our application helps you decide the best place to eat based on the collaborative preferences of you and your friends. The algorithm.py code implements the core algorithm we will be using. It is a modified topic specific page rank implementation that factors in history, shared user cuisine preferences, and links between preferred businesses based on food cuisine. This example displays our approach without the use of the actual data. Due to license restrictions the sample data we are using could not be publicly displayed. Therefore we created a very limited subset of sample data to demonstrate our algorithm. Also, our core algorithm will be using mysql instead of sqlite, because of performance considerations. However, for ease in demonstration purposes sqlite was used for the checkpoint.
#Dependencies
Please make sure the following is installed:

Python2 with json library

Sqlite3

#Execution:
Simply copy the files located here to your local machine and execute the run.sh script.
