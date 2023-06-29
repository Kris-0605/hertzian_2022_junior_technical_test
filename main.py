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
                return requests.get(endpoint, json=json if json else None, params=url_encoded if url_encoded else None)
            except:
                time.sleep(self.RETRY_DELAY) # Maybe we're getting rate limited?
        raise requests.ConnectionError(f"Something went wrong connecting to {endpoint} with JSON input {json} and URL encoded input {url_encoded}")

    def follow_cursor(self,
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
            request_json = self.__make_request(endpoint, json=json, url_encoded=url_encoded).json()
            for x in data_key(request_json):
                self.data.append(x)
            try: # Get the cursor if it exists, otherwise terminate
                if (c := cursor_key(request_json)) == cursor:
                    break
                else:
                    cursor = c
            except:
                break
        return self.data
    
    def __filter_reviews(self, date1, date2, timestamp_key=lambda entry: entry["timestamp"]):
        '''
        The task to "only crawl between two dates" confuses me, because the Steam API doesn't let you do that.
        Instead, you'd have to crawl until that date, and then filter out the ones you didn't want.
        So, that's what this function does.
        '''
        pass

    def __sort_reviews(self):
        pass

    def dump_json_out(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.data, f, indent=4)

class SteamReviewCrawler(ReviewCrawler): # Inherits from ReviewCrawler, only contains methods specific to Steam
    def __init__(self, appID, franchise, gameName):
        self.__franchise, self.__gameName = franchise, gameName
        self.follow_cursor(
            f"https://store.steampowered.com/appreviews/{appID}",
            url_encoded={"json": "1", "num_per_page": "100", "filter": "updated"}, # More could be specified, but nothing was given in the PDF, I would ask about more if this was the real thing
            cursor="*",
            completion_condition=lambda review_crawler: len(review_crawler.data) >= 5000,
        )
        self.data = self.__process_data(self.data)
    
    def __process_data(self, old_data):
        "Formats the raw JSON into the right format"
        new_data = []
        ids = set()
        review_counter = 0
        for x in old_data:
            time_obj = time.localtime(x["timestamp_updated"]) # Could be changed to created, but was not specified and this seemed more useful
            id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(x["recommendationid"]))) # Generates version 5 UUID from unique recommendation ID
            if id not in ids:
                new_data.append({
                    "id": id,
                    "author": str(uuid.uuid5(uuid.NAMESPACE_DNS, str(x["author"]["steamid"]))), # Generates version 5 (hased, unreversible) UUID from unique steam user ID
                    "date": f"{time_obj.tm_year}-{time_obj.tm_mon:02}-{time_obj.tm_mday:02}", # Formatting into yyyy-mm-dd format
                    "hours": int(x["author"]["playtime_at_review"]), # Could be changed to playtime_forever, not specified, this seemed more useful
                    "content": x["review"],
                    "comments": int(x["comment_count"]),
                    "source": "steam",
                    "helpful": int(x["votes_up"]),
                    "funny": int(x["votes_funny"]),
                    "recommended": x["voted_up"],
                    "franchise": self.franchise,
                    "gameName": self.gameName,
                })
                ids.add(id)
            review_counter += 1
            if review_counter == 5000:
                # Could I do this with return new_data[:5000]? Yes. However that would take longer, so yes this if statement is messy but it's for the greater good.
                break
        return new_data
    
    # It's not foolproof and it looks a bit messy and can be broken, but getters is the only way to ensure that
    # the attributes haven't been modified so we can ensure the attributes are the same as at function invocation
    @property
    def franchise(self):
        return self.__franchise
    
    @property
    def gameName(self):
        return self.__gameName


# A pipeline like this will probably already exist, but I made a simple one for this project
def run_tests(tests: tuple, verbose=True, continue_on_failure=True) -> bool:
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
    START_TIME = 1625008316 # 2 years ago today
    END_TIME = 1656544316 # 1 year ago today
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
        # Stretch goals!
        # Checks that all entries are between the given dates
        # In hindsight I probably could've used this formatting tool instead of writing my own code for it
        lambda: all(START_TIME <= time.mktime(time.strptime(x["date"], "%Y-%m-%d")) <= END_TIME for x in data),
        # Checks that data is equivalent to the same data sorted first by date, then by ID
        lambda: data == sorted(data, key=lambda x: (time.mktime(time.strptime(x["date"], "%Y-%m-%d")), x["id"])),
    )
    if run_tests(tests):
        print("All tests ran successfully.")
        return True
    else:
        print("Something went wrong, at least one test failed.")
        return False

if __name__ == "__main__":
    execute_steam_tests()