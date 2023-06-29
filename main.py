import json
import time
import uuid
import requests

class ReviewCrawler: # Generic crawler
    NUMBER_OF_RETRIES = 5
    RETRY_DELAY = 1

    def __make_request(self, endpoint: str, json={}, url_encoded={}) -> dict:
        '''
        Makes request to endpoint with JSON and/or URL encoded data if necessary
        If errors, retries for self.NUMBER_OF_RETRIES before raising an error
        Upon retry, waits for self.RETRY_DELAY seconds before retrying
        JSON and URL encoded data should be dictionaries
        '''
        # I know I don't have to include JSON encoding for this task, but it's common for API endpoints
        # and it would save someone from having to change the code to add it later for another site
        for _ in range(self.NUMBER_OF_RETRIES):
            try:
                return requests.get(endpoint, json=json if json else None, data=url_encoded if url_encoded else None)
            except:
                time.sleep(self.RETRY_DELAY) # Maybe we're getting rate limited?
        raise requests.ConnectionError(f"Something went wrong connecting to {endpoint} with JSON input {json} and URL encoded input {url_encoded}")

    def __follow_cursor(self,
                      endpoint: str,
                      json={},
                      url_encoded={},
                      cursor=None,
                      cursor_key=lambda raw_data: raw_data["cursor"],
                      data_key=lambda raw_data: raw_data["reviews"],
                      completion_condition=None,
                      cursor_injection=lambda json, url_encoded, cursor: url_encoded.update({"cursor": cursor}),
                      ) -> list:
        '''
        API endpoints will often have a cursor, where you get your next batch of results by passing the cursor into the next request
        This function does that for you until completion_condition is met or the cursor is is not found in the returned data
        endpoint, json and url_encoded are all data to pass to the make_request method
        cursor is the value that should be passed on the first call, if any
        cursor_key is a lambda function that gets the key from the JSON data returned by the request, and by default checks the "cursor" key
        data_key is a lambda function that points to where the JSON array of reviews is, and by default checks the key "reviews"
        completion_condition is a lambda function used to terminate if a condition is met, such as if a certain number of reviews have been collected.
        completion_condition should take a single parameter, being the ReviewCrawler object (self).
        It should return True to terminate, or False otherwise.
        cursor_injection is a lambda function that takes three parameters, being the JSON data, url_encoded data and the value of the cursor.
        This lambda function defines where the cursor data should be used in the next request, and by default it adds the cursor to the URL encoded data.
        This function assumes the data at data_key is in a JSON array of reviews, and returns a list of all entries in those JSON arrays merged into one list of all the entries.
        '''
        self.data = []
        while (not completion_condition(self)) if completion_condition else True: # Execute if completion_condition is False, or if there is no completion_condition
            if cursor: # If there is no cursor, this will skip injection on the first request
                cursor_injection(json, url_encoded, cursor)
            # Variable not required, but nice for readability
            request_json = self.make_request(endpoint, json=json, url_encoded=url_encoded).json()
            for x in data_key(request_json):
                self.data.append(x)
            try: # Get the cursor if it exists, otherwise terminate
                cursor = cursor_key(request_json)
            except:
                break
        return self.data

    def dump_json_out(self, filename: str):
        pass

class SteamReviewCrawler(ReviewCrawler): # Inherits from ReviewCrawler, only contains methods specific to Steam
    def __init__(self, appID, franchise, gameName):
        self.__franchise, self.__gameName = franchise, gameName
    
    # It's not foolproof and it looks a bit messy and can be broken, but getters is the only way to ensure that
    # the attributes haven't been modified so we can ensure the attributes are the same as at function invocation
    @property
    def franchise(self):
        return self.__franchise
    
    @property
    def gameName(self):
        return self.__gameName


# A pipeline like this will probably already exist, but I made a simple one for this project
def run_tests(tests: tuple[function], verbose=True, continue_on_failure=True) -> bool:
    '''
    Runs tests, returns a boolean True or False of whether they were successful.
    Expects iterable of functions, functions are tests to be ran.
    Test functions should output a boolean True or False, True means test succeeded, False means it failed.
    verbose == True means printing on test success, verbose == False means printing only on failure
    continue_on_failure == True means run all tests, continue_on_failure == False means exit if a test fails
    '''
    success = True
    for num, test in enumerate(tests, start=1):
        # Could be modified to input arguments into test function, but not needed in this case
        if test(): # Test succeeded
            if verbose:
                print(f"Test {num} succeeded")
        else: # Test failed
            success = False
            print(f"Test {num} failed")
            if not continue_on_failure:
                break
    return success

def execute_steam_tests():
    crawler = SteamReviewCrawler("1382330", "Persona", "Persona 5 Strikers") # Nice, I looked up the appID
    crawler.dump_json_out("1382330.json")
    with open("1382330.json", "r") as f:
        data = json.load(f)
    tests = (
        lambda: len(data) <= 5000, # "no more than 5000 reviews"
        # "Franchise, gameName, and source are defined at function invocation."
        lambda: len(set(x["franchise"] for x in data)) == 1 and data[0]["franchise"] == crawler.franchise, # All franchises are the same, and the same as at function invocation
        lambda: len(set(x["gameName"] for x in data)) == 1 and data[0]["gameName"] == crawler.gameName,
        lambda: len(set(x["source"] for x in data)) == 1 and data[0]["source"] == "steam", # All sources are "steam"
        # Verify data types are correctly and reasonable, if not listed here then errors will be raised by other tests
        lambda: all(type(x["hours"]) == int for x in data), # Data type integer for the "hours" of all reviews
        lambda: all(type(x["comments"]) == int for x in data),
        lambda: all(type(x["helpful"]) == int for x in data),
        lambda: all(type(x["funny"]) == int for x in data),
        lambda: all(type(x["recommended"]) == bool for x in data), # Data type boolean for the "recommended" of all reviews
        lambda: all(type(x["content"]) == str for x in data), # Data type boolean for the "content" of all reviews
        # Verify date in yyyy-mm-dd format
        # The actual format is not specified, this is just my best guess from looking at the format given in the example.
        # Had this been an actual technical test instead of a practice, I would have emailed someone to ask
        lambda: all(len(x["date"]) == 10 for x in data), # Check string length is 10
        lambda: all(x["date"][4] == "-" for x in data), # Check for hyphens in 5th and 8th characters
        lambda: all(x["date"][7] == "-" for x in data),
        # Checks that first 4 characters of the date in every entry is within the range of Steam's launch in 2003, and next year (in case it's New Years Eve and timezones)
        lambda: all(2003 <= int(x["date"][:4]) <= time.localtime().tm_year + 1 for x in data),
        # Check that the month is between 1 and 12 inclusive by checking the 6th and 7th characters
        lambda: all(1 <= int(x["date"][5:7]) <= 12 for x in data),
        # Check that the day is between 1 and 31 inclusive by checking the last 2 characters
        lambda: all(1 <= int(x["date"][8:]) <= 31 for x in data),
        # Verify that "author" and "id" are in UUID format
        lambda: all(uuid.UUID(x["author"], version=5) for x in data), # Will raise ValueError if a UUID is invalid
        lambda: all(uuid.UUID(x["id"], version=5) for x in data),
        # Verify that "id" is unique
        lambda: len(set(x["id"] for x in data)) == len(data),
        # Then all that's left is OOP, which I don't think I can reasonably test with a function, and the stretch goals which will be added later
    )
    if run_tests(tests):
        print("All tests ran successfully.")
        return True
    else:
        print("Something went wrong, at least one test failed.")
        return False

if __name__ == "__main__":
    pass