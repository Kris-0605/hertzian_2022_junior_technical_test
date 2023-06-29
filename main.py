import json
import time
import uuid

class ReviewCrawler: # Generic crawler
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
    data = json.load("1382330.json")
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