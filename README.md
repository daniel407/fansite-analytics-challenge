# Table of Contents
1. [Background](README.md#background)
2. [Running the program](README.md#running-the-program)
3. [Dependencies](README.md#dependencies)
4. [Generated output](README.md#generated-output)
5. [Completed testing](README.md#completed-testing)


# Background

This is a code submission for the fansite analytics challenge (4/5/2017).
Author: Daniel Schweigert

# Running the program
The programm can be executed by running 
./run.sh
which will use python3 to execute the file /src/process_log.py

# Dependencies
The script requires no further installations of libraries or packages and will run solely using built-in functions of Python 3. The python version used to test the script was 3.4.3.
The script will not properly execute in Python 2.

# Generated output
Running the script will generate a number of output files whose contents aim to meet the specifications of the task features 1-4 and additional features 5 and 6. Features 1-4 have been specified in the original task description and are therefore not covered in this document. For features 5 and 6, the description is provided further down in this paragraph. 

### Feature 1: 
The data generated for feature 1 can be found in ./log_output/hosts.txt

### Feature 2: 
The data generated for feature 2 can be found in ./log_output/resources.txt

### Feature 3: 
The data generated for feature 3 can be found in ./log_output/hours.txt  

### Feature 4: 
The data generated for feature 4 can be found in ./log_output/blocked.txt 

### Feature 5:
The data generated for feature 5 can be found in ./log_output/incomplete.txt 

Feature 5 involves the logging of all log record instances which are uninterpretable or incomplete. Certain log record instances do not contain readable or incomplete information which raise a custom exception IncompleteLogRecordError during the parsing of the log file. Incomplete record instances will be logged in the output file for further review.

### Feature 6:
The data generated for feature 6 can be found in ./log_output/stats.txt

Feature 6 provides a list of statistics extracted from the log file. The following metrics are computed and logged in the output file:
    - First timestamp
    - Last timestamp
    - Total unique hosts
    - Total requests
    - Average number of requests per day


# Completed testing
The program passes the tests which were included in the original task environment.

Furthermore, another set of 4 tests were created by the author in order to test for special cases and provide a more thorough testing on the deliverables of the individual features.
