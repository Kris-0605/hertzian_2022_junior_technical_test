# Steam Review API Crawler Technical Test

Step 1: pip install -r requirements.txt (or pip install requests)

Step 2: Run main.py

Step 3: Do what it says!

Entering "test" will run unit tests for Persona 5 Strikers, and output the result to 1382330.json, which you should already find in this repository.

Entering "appID,franchise,gameName" (example: "411370,Melty Blood,Melty Blood Actress Again Current Code") will get the 5000 most recent reviews for that app ID.

Entering "appID,franchise,gameName,start_yyyy-mm-dd,end_yyyy-mm-dd" (example: "411370,Melty Blood,Melty Blood Actress Again Current Code,2023-01-01,2023-06-29") will filter to just those dates.

As for evidence of testing, you'll find the testing results at various stages in the "test_output.txt file, which is something I manually update with the output and comments on what it means.

I understand that it's not perfect, for example I used requests instead of aiohttp, making it suboptimal for an asynchronous pipeline, but I thought it was reasonable given the guidelines I was given. Please let me know if you have any feedback or improvements, especially since this is my first time trying to use test driven development. Thank you!
