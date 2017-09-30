# -*- coding: utf-8 -*-
"""
Created on Wed May  3 16:34:04 2017

@author: Houssam
"""
import datetime
import time
from datetime import timedelta
from parsing import CHECKING_TIME, TRAFFIC_LIMIT

# SIMULATOR PARAMETERS 

UTC = '+0100' # Paris UTC
# If we write a line every time_reference=SPEED_LIMITATION, it will 
# generate exactly a number=TRAFFIC_LIMIT of lines every CHECKING_TIME
SPEED_LIMITATION = CHECKING_TIME / TRAFFIC_LIMIT 

class Simulator:
    
    """Simulate a log file been actively written to

    This class has a very important attribute :  it will
    represent "speed limitation", when writing a line every 
    time (=time_reference), it will will be exactly the limit
    to trigger the traffic ALERT. That is to say, if we write
    each time (when time > time_reference) we will be under
    speed limitation and therefore not trigger the alert. 
    if we write at each time (when time < time_reference) we 
    will be above speed limitation and therefore trigger the alert.

    We will be writing a file where normal traffic will be simulated 
    at the beginnig, then high traffic so see the alert, and then we will
    simulate normal traffic again so see the traffic recovering.

    Attributes:
        path (str): The path of the file to write to
        time_reference (int): indicator for speed limitation
        working (bool): Condition in the while loop of the method

    """
    def __init__(self, path):
        """ 

        Args:
            path (str): The path of the file to write to

        """
        self.path = path
        self.time_reference =  SPEED_LIMITATION
        self.working = True
    
    
    def terminate(self):
        """ Ending the loop

        """
        self.working = False

    def worker(self):
        """Creates an artificial log file by writing lines in the file

        It is the target argument in simulator thread attribute in 
        Monitor class. It has a while loop that ends when the 3 CHECKING_TIME
        periods are over. Last period ends after 3.5* CHECKING_TIME in order
        to let time to recover.

        First period is normal traffic, second is high traffic, and last one
        is normal. We try to simulate several cases, with several status
        possibilities, and size, in order to display interesting statistics.

        Raises:
            IOError when the log file can not be accessed 
            or fails at opening it
            Potiental errors occuring after trying
        """
        with open(self.path,'w') as f:
            try:
                start_time = timedelta(
                               hours=datetime.datetime.now().time().hour,
                               minutes=datetime.datetime.now().time().minute,
                               seconds=datetime.datetime.now().time().second)
                current_time = start_time
                tdelta = current_time - start_time

                # Normal traffic simulation
                # First period

                while tdelta.total_seconds() < CHECKING_TIME and self.working:

                    f.write('10.0.0.153 user-identifier frank ['
                     + datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S ')
                     + UTC 
                     + '] "GET /twiki/bin/attach/ HTTP/1.1" 200 2326\n')

                    time.sleep(self.time_reference*1.2) 
                        # We are 1/1.2 times under the speed limitation 

                    # We have to re-initialize variables in order to have 
                    # current time
                    # Flush everything in the buffer

                    f.flush()
                    current_time = timedelta(
                               hours=datetime.datetime.now().time().hour,
                               minutes=datetime.datetime.now().time().minute,
                               seconds=datetime.datetime.now().time().second)
                    tdelta = current_time - start_time

                # High traffic simulation
                # Second period

                while tdelta.total_seconds() < 2*CHECKING_TIME and self.working:

                    f.write('194.168.0.10 - - ['
                     + datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S ')
                     + UTC 
                     + '] "GET /twiki/bin/ HTTP/1.1" 200 2326\n')

                    time.sleep(self.time_reference/2)
                        # We are 2 times above the speed limitation

                    f.write('127.0.0.1 user-identifier frank ['
                      + datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S ') 
                      + UTC
                      + '] "GET /robots.txt HTTP/1.1" 500 2326\n')

                    time.sleep(self.time_reference/6)
                        # We are 6 times above the speed limitation

                    f.write('127.0.0.1 user-identifier frank ['
                      + datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S ') 
                      + UTC
                      + '] "GET /robots.txt HTTP/1.1" 200 2326\n')

                    time.sleep(self.time_reference/12)
                        # We are 12 times above the speed limitation

                    f.write('64.242.88.10 user-identifier frank ['
                      + datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S ')
                      + UTC
                      + '] "GET /cgi-bin/mailgraph2.cgi HTTP/1.1" 400 2048\n')

                    time.sleep(self.time_reference/3)
                        # We are 3 times above the speed limitation

                    # We have to re-initialize variables in order to have 
                    # current time
                    # Flush everything in the buffer
                    
                    f.flush() 
                    current_time = timedelta(
                             hours=datetime.datetime.now().time().hour,
                             minutes=datetime.datetime.now().time().minute,
                             seconds=datetime.datetime.now().time().second)
                    tdelta = current_time - start_time
                              
                # Normal traffic
                # Third period
                # 3.5 because we need time to recover from alert

                while tdelta.total_seconds() < 3.5*CHECKING_TIME and self.working:
                  
                    f.write('127.0.0.1 user-identifier frank ['
                     + datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S ')
                     + UTC
                     + '] "GET /apache_pb.gif HTTP/1.1" 200 2326\n')

                    time.sleep(self.time_reference*1.1)
                        # We are slightly under speed limitation

                    # We have to re-initialize variables in order to have 
                    # current time
                    # Flush everything in the buffer

                    f.flush() 
                    current_time = timedelta(
                               hours=datetime.datetime.now().time().hour,
                               minutes=datetime.datetime.now().time().minute,
                               seconds=datetime.datetime.now().time().second)
                    tdelta = current_time - start_time
                
            except IOError:
                raise
                print("Can't write logs to destination file")
                self.terminate()