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