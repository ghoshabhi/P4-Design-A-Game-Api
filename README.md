************** Tic Tac Toe API*****************

This project is based on the Google App Engine Technology and provides a backend API for the popular Game -  "Tic Tac Toe"! The basic rules of the Game are very simple - this is a multiplayer game. So one of the player is "O" and the other is "X". Both the players get alternate chances to fill in one position on the board(3x3). The player who has either vertical, horizontal or diagnol cells filled up with his letter becomes the winner!

Prerequisites :
	1. Python 2.7
	2. Google App Engine Launcher v1.9.x and above

To Run the project :
	1. Go to app.yaml and change the first line with your Project ID
	2. Next, download and install the Google App Engine Launcher from this link : https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python
	3. Once you have successfully installed the Google App Engine console, go to File(top left corner) and choose "Add Existing Application"
	4. Choose the location of the Project
	5. Once you see that your project has been added to the console, you could test it Locally by clicking on "Run" or to deploy it on the Google servers hit "Deploy".
	6. If your application exits with an "exit code(0)", that means your application was successfully deployed and you could check it working live on : your-project-id.appspot.com. Since this is only an API, there is no front end to the application, to visit the APIs explorer enter this URL : your-project-id.appspot.com/_ah/api/explorer
	7. After you visit the APIs explorer you can see the various endpoints methods. 
	8. Along with each method are the required input parameters given so that the users know what data to enter.

Rules of the Game :
	1. Each player is assigned one letter : either "X" or "O"
	2. Each player takes alternate chances to fill in the available space on the board.
	3. The board is a 3x3 grid, so the player has 9 cells to choose from at the very first attempt.
	4. Winner of the game is decided when either consecutive horizontal or vertical cells(3) are filled with the same letter of either of the players.
		Possible winning positions :
		X|X|X     | |      | |      X| |      |X|      | |X       X| |        | |X
		 | |     X|X|X     | |      X| |      |X|      | |X        |X|        |X| 
		 | |      | |     X|X|X     X| |      |X|      | |X        | |X      X| | 

Scoring Rules :
	1. Each player is awarded + 1 point for winning the game and 0 points for losing one
	2. In case of a draw, no player is awarded any points