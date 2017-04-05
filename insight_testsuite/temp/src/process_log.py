# -*- coding: utf-8 -*-

import sys
import re
import datetime
import codecs
import operator


class IncompleteLogRecordError(ValueError):
    """
    Custom type of ValueError.
    Used for instances of incomplete log information (feature 5).
    """
    pass


def parse_log_record(record):
    """
    Interprets a log record line and returns values for
    host, timestamp, reqequest type, resource, response code and byte load.

    Args:
    record (str) : unicode string representing one line in log.txt

    Returns:
    host (str) : hostname or internet address
    timestampe (str) : format DD/MON/YYYY:HH:MM:SS -0400
    req (str) : type of http request
    resource (str): requested resource
    code (str) : http reply code
    byte (int) : bytes in the reply

    Raises:
    IncompleteLogRecordError : if record does not contain all log information.
    """

    # cleaning
    record = record.strip()

    # parse response string and split by request type and resource
    response_re = re.findall('[“"](.*?)[”"]', record)
    if len(response_re) < 1:
        raise IncompleteLogRecordError(record)
    response = response_re[0]
    response_split = response.split(' ')
    if len(response_split) < 2:
        raise IncompleteLogRecordError(record)
    req, resource = response_split[0], response_split[1]

    # host
    splits = record.split(' ')
    host = splits[0]

    # byte will be allocated 0, if '-'
    byte = 0 if '-' in splits[-1] else int(splits[-1])

    # response code
    code = splits[-2]

    # timestamp
    time_re = re.search('\[(.*?)\]', record)
    timestamp = time_re.group(1)

    return host, timestamp, req, resource, code, byte


def item_swap(item):
    """
    Helper function used for sorting. It is used as the key function in the
    sorting and helps sorting for highest count and lowest lexigraphic
    ordering.

    Args:
    item (tuple) : iterable with at least 2 items

    Returns:
    tuple : tuple with swapped order of 0th and 1st item
    """
    return (-item[1], item[0])


def sort_and_select(visits):
    """
    Helper function used for feature 3.
    The dictionary visits will be sorted based on count (items). Afterwards,
    the size of the dictionary will be reduced to retain only the 10 highest
    counts.

    Args:
    visits (dictionary) : dictionary to maintain visit counts by timestamp

    Returns:
    visits (dictionary) : updated visit counts
    """
    sorted_visits = sorted(
        visits.items(),
        key=operator.itemgetter(1),
        reverse=True)
    max_len = 10 if len(sorted_visits) > 10 else len(sorted_visits)
    visits = {}
    for i in range(max_len):
        visits[sorted_visits[i][0]] = sorted_visits[i][1]
    return visits


def sort_by_count_and_lexi(d):
    """
    Sorts a dictionary by decending value order followed by ascending key
    order.

    Args:
    d (dictionary)

    Returns:
    d (dictionary) : sorted dictionary
    """
    sorted_visits = sorted(d.items(), key=item_swap, reverse=False)
    return sorted_visits


def window_count(tx, recent):
    """
    Helper function for feature 3.
    Counts how many elements of the list recent are within 60min window with
    tx.

    Args:
    tx (datetime.datetime)
    recent (list)

    Returns:
    int : count
    """
    i = 1
    while (recent[-i] - tx).total_seconds() > 3600:
        i += 1
    return len(recent) - i + 1


def update_count(recent, visits):
    """
    Helper function for feature 3.
    Removes first item of recent timestamp list and logs counts of events
    within 60min window. Additionally logs counts for all timestamps between
    first and second item of recent.

    Args:
    recent (list)
    visits (dictionary)

    Returns:
    visits (dictionary) : updated counts
    """
    ti = recent.pop(0)
    if ti not in visits:
        visits[ti] = window_count(ti, recent) + 1
    for s in range(1, int((recent[0] - ti).total_seconds())):
        tj = ti + datetime.timedelta(seconds=s)
        if tj not in visits:
            visits[tj] = window_count(tj, recent)

    return visits


def product_sort(d):
    """
    Sorts the contents of dictionary d first by values. Afterwards, takes the
    top ten elements and sorts them lexicographically by keys.

    Args:
    d (dictionary)

    Returns:
    sorted_d_list (list)
    """
    sorted_d_list = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
    max_len = 10 if len(sorted_d_list) > 10 else len(sorted_d_list)
    sorted_d_list = sorted_d_list[0:max_len]
    sorted_d_list = sorted(sorted_d_list, key=item_swap, reverse=False)
    return sorted_d_list


# path allocations
log_file_path = sys.argv[1]
host_output_file_path = sys.argv[2]
hours_output_file_path = sys.argv[3]
resources_output_file_path = sys.argv[4]
blocked_output_file_path = sys.argv[5]
incomplete_output_file_path = sys.argv[6]
stats_output_file_path = sys.argv[7]

# data structures
host_counts = {}
resource_volumes = {}
recent = []
visits = {}
blocked_hosts = {}
failed_logins = {}
t_first = None
t_last = None

# open files
f = codecs.open(log_file_path, mode='r', encoding='utf-8', errors='replace')
fo_blocked = open(blocked_output_file_path, 'w')
fo_incomplete = open(incomplete_output_file_path, 'w')

# one pass through the log file. relevant information for the respective
# features is stored in the respective data structures
for line in f:

    # extracting information from log file record. Incomplete records will
    # be logged (feature 5)
    try:
        host, timestamp, request, resource, code, byte = parse_log_record(line)
    except IncompleteLogRecordError as ilre:
        fo_incomplete.write(str(ilre))
        fo_incomplete.write('\n')
        continue

    # Feature 1:
    # host counting
    host_counts[host] = host_counts.get(host, 0) + 1

    # Feature 2:
    # resource volumne counting
    resource_volumes[resource] = resource_volumes.get(resource, 0) + byte

    # Feature 3:
    # counting visits within 60min window from timestamp
    t0 = datetime.datetime.strptime(timestamp, "%d/%b/%Y:%H:%M:%S %z")
    recent.append(t0)
    while len(recent) > 1 and (recent[-1] - recent[1]).total_seconds() > 3600:
        visits = update_count(recent, visits)
        visits = sort_and_select(visits)

    # Feature 4: blocking
    # case: host is on blocked_host dictionary. Update blocked_host based on
    # timestamp. Add to outputfile if applicable
    if host in blocked_hosts.keys():
        # if host has been on blocked list for more than 5 min (300s),
        # remove from blocked list
        # otherwise, write host to output file
        if (t0 - blocked_hosts[host]).total_seconds() > 300:
            blocked_hosts.pop(host)
        else:
            fo_blocked.write(line)

    # update failed_logins, based on timesetamps
    failed_hosts = list(failed_logins.keys())[:]
    for failed_host in failed_hosts:
        failed_attempts = failed_logins[failed_host]
        for failed_attempt in failed_attempts:
            if (t0 - failed_attempt).total_seconds() > 20:
                failed_attempts.remove(failed_attempt)
        if len(failed_attempts) == 0:
            failed_logins.pop(failed_host)

    # case: host is not on blocked list. Update failed_logins
    if host not in blocked_hosts.keys():

        # case: failed login attempt. Update failed_logins. Move to
        # blocked_hosts, if applicable
        if code == '401':
            failed_attempts = failed_logins.get(host, [])
            failed_attempts.append(t0)
            failed_logins[host] = failed_attempts

            if len(failed_logins[host]) >= 3:
                failed_logins.pop(host)
                blocked_hosts[host] = t0

        # case: successful login attempt. Remove host if on failed_logins.
        if (host in failed_logins) and resource == '/login' and code == '200':
            failed_logins.pop(host)

    # feature 6: stats
    # capturing first and last timestamp
    if t_first is None:
        t_first = t0
    t_last = t0

# close files
fo_incomplete.close()
fo_blocked.close()
f.close()


# Post processing of data structures which were populated during the pass

# For feature 1:
# sorting host counts and outputting ten most frequently visiting hosts
# into file.
sorted_host_counts = product_sort(host_counts)
with open(host_output_file_path, 'w') as fo:
    for i in range(len(sorted_host_counts)):
        fo.write(str(sorted_host_counts[i][0]) +
                 ',' + str(sorted_host_counts[i][1]))
        fo.write('\n')

# For feature 2:
# sorting resources by volume and printing into file
sorted_resource_volumes = product_sort(resource_volumes)
with open(resources_output_file_path, 'w') as fo:
    for i in range(len(sorted_resource_volumes)):
        fo.write(sorted_resource_volumes[i][0])
        fo.write('\n')

# For feature 3:
# allocate last visits into the counter until list of recent is empty
while len(recent) > 1:
    visits = update_count(recent, visits)
    visits = sort_and_select(visits)

sorted_visits = sort_by_count_and_lexi(visits)

# For feature 3
# log the strict ordering of 10 timestamps with highest visit count (feature 3)
max_len = 10 if len(sorted_visits) > 10 else len(sorted_visits)
with open(hours_output_file_path, 'w') as fo:
    for i in range(max_len):
        fo.write(sorted_visits[i][0].strftime(
            "%d/%b/%Y:%H:%M:%S %z") + ',' + str(sorted_visits[i][1]))
        fo.write('\n')

# For feature 4:
# No extra code. This feature is handled during the pass through the log file

# For feature 5:
# No extra code. This feature is handled during the pass through the log file

# For feature 6:
# open stats file
fo_stats = open(stats_output_file_path, 'w')

# log first and last timestamp
fo_stats.write('First timestamp: ')
fo_stats.write(t_first.strftime("%d/%b/%Y:%H:%M:%S %z"))
fo_stats.write('\n')
fo_stats.write('Last timestamp: ')
fo_stats.write(t_last.strftime("%d/%b/%Y:%H:%M:%S %z"))
fo_stats.write('\n')

# compute and log total number of requests and hosts
total_requests = 0
total_unique_hosts = 0
for host in host_counts:
    total_unique_hosts += 1
    total_requests += host_counts[host]
fo_stats.write('Total unique hosts: ')
fo_stats.write(str(total_unique_hosts))
fo_stats.write('\n')
fo_stats.write('Total requests: ')
fo_stats.write(str(total_requests))
fo_stats.write('\n')

# compute and log number of requests per day
total_time_s = float((t_last - t_first).total_seconds())
total_time_d = total_time_s / (24 * 60 * 60)
requests_per_day = round(total_requests / total_time_d, 1)
fo_stats.write('Average number of requests per day: ')
fo_stats.write(str(requests_per_day))
fo_stats.write('\n')

# close stats file
fo_stats.close()
