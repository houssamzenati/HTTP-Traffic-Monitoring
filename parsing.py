# -*- coding: utf-8 -*-
"""
Created on Wed May  2 21:24:55 2017

@author: Houssam
"""

import re
import datetime

# CONSTANT PARAMETERS 

CHECKING_TIME = 2*60  # time for checking sections
HITS_TIME = 10  # time for reporting on most hit section       
TRAFFIC_LIMIT = 42  # limit for triggering an alert on traffic
# Time to wait when there is no more line to read in log file
LOG_WAITING_TIME = 2 * CHECKING_TIME // TRAFFIC_LIMIT                                                   
NUMBER_SECTIONS = 1


    
def get_common_log_format(string_log):
    """Gets the common log format of a log
    
    Args: 
        string_log (str): Is the access log currently analyzed in the queue

    Returns:
        list: Using a list to refer more easily to each element
        None: If the log_file does not match the format

    Example:
        127.0.0.1 user-identifier frank [10/Oct/2000:13:55:36 -0700] /
        ip        rfc_id          user_id date                                        
        "GET /apache_pb.gif HTTP/1.0" 200 2326
        request                       status size
    """ 
    p = re.compile(
        '([^ ]*) ([^ ]*) ([^ ]*) \[([^]]*)\] "([^"]*)" ([^ ]*) ([^ ]*)')
    m = p.match(string_log)
    if m is not None:
        ip, rfc_id, user_id, date, request, status, size = m.groups()
        # Using a list to refer more easily to each element
        return [ip, rfc_id, user_id, date, request, status, size]
  

def get_section(string_log):
    """Gets the section from the request of an access log file
    
    Args: 
        string_log (str): Is the access log currently analyzed in the queue

    Returns:
        str: The section in access log line
        None: In specific cases

    Note:   
        Returns None when access log line is not appropriate
        
    """ 
    try:
        section = get_common_log_format(string_log)[4]
        if section != None and section != '':
            parts = section.split(' ')
            try :
                parts = parts[1] #getting the section
                parts = parts.split('/')
                parts = parts[1:3]
                section = '/'.join(parts)
                return section
            except IndexError:
                return None
    except TypeError:
        return None

            
def get_time(string_log):
    """Gets the time of an access log file
    
    Args: 
        string_log (str): Is the access log currently analyzed in the queue

    Returns:
        time: The time in access log line in time type for computations
        time: If get_common_log_format is None or string_ log is empty 
              it returns the current time

    Note:   
        Returning the current time is an approximation when parsing actively
        written log file
        It is not a problem when analyzing sample files which are already 
        written because specific case therefore appears only at the end
        
    """    
    if string_log != None and string_log != '':
        try:
            date = get_common_log_format(string_log)[3]
            parts = date.split(' ')
            parts.remove(parts[-1])
            date =' '.join(parts)
            dt = datetime.datetime.strptime(date, "%d/%b/%Y:%H:%M:%S")
            return dt.time()
        except TypeError:
            return datetime.datetime.now().time()
    else : 
        return datetime.datetime.now().time()                                     


def get_status(string_log):
    """Gets the status from the access log file line
    
    Args: 
        string_log (str): Is the access log currently analyzed in the queue

    Returns:
        tuple: See cases in comments

    Note:   
        Returns None when access log line is not appropriate
        
    """ 
    try:
        status=get_common_log_format(string_log)[5]
        if status.startswith('2'):
            return (1,0,0,0) #successfull
        if status.startswith('3'):
            return (0,1,0,0) #redirection
        if status.startswith('4'):
            return (0,0,1,0) #client error
        if status.startswith('5'):
            return (0,0,0,1) #server error
    except:
        return None

def get_size(string_log):
    """Gets the size (bytes) from a request in a access log file line
    
    Args: 
        string_log (str): Is the access log currently analyzed in the queue

    Returns:
        int: Number of bytes of the request
        int: 0 if no infos
        
    """ 
    try:
        size=get_common_log_format(string_log)[6]
        return int(size)
    except:
        return 0

def get_ip(string_log):
    """Gets the ip from the access log file line
    
    Args: 
        string_log (str): Is the access log currently analyzed in the queue

    Returns:
        str: The ip adress
        None: In specific cases

    Note:   
        Has not been needed for the moment, maybe later.
        
    """ 
    try:
        ip=get_common_log_format(string_log)[0]
        return ip
    except:
        return None