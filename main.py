# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 14:59:21 2017

@author: Houssam
"""

import datetime
import threading
import time
import queue
import operator

from datetime import timedelta
from simulator import Simulator
from parsing import *

   
class Scan:

    """Scans log from an active log file and adds it to the queue logs

    This class scan a log file and adds every log line in a queue
    It has a method that is a target of a thread used for analyzing
    actively written file. 

    Attributes:
        working (bool): Condition in the while loop of the method
        logs (queue.Queue): Queue structure is thread-safe
        path (str): The path for openning file

    """

    def __init__(self,logs, path):
        """ 

        Args:
            logs (qeue.Queue): Is the queue created in the Monitor class

        """
        self.working = True
        self.logs = logs
        self.path = path

    def terminate(self):
        """ Ends the process of scanning, is used in the worker while loop 

        """
        self.working = False

    def worker(self):
        """Worker is target in the tread used in Monitor class

        It has a while loop that ends when waiting 2 times the time
        needed in Simulating process. A good time could be 15 to 20s.
        The scanner resolution is one second. Every second, the loop
        tests if there is a line in the file actively written.

        Raises:
            IOError when the log file can not be accessed
            Other exceptions when log format doesn't match

        """
        try:
            with open(self.path, 'r+') as f:
                # Time origin for beginning to scan
                last_scan_time = timedelta(
                                  hours=datetime.datetime.now().hour, 
                                  minutes=datetime.datetime.now().minute,
                                  seconds=datetime.datetime.now().second)
                while self.working:
                    line = f.readline()
    
                    # If it can find a line in the file
                    if line != '':
                        try:
                            self.logs.put(line)
                            # Last time a scan occured
                            last_scan_time = timedelta(
                                 hours=datetime.datetime.now().hour, 
                                 minutes=datetime.datetime.now().minute,
                                 seconds=datetime.datetime.now().second)
                            
                        except:
                            f.close()
                            self.terminate()
                            raise

                    # If it did not find a line in the file
                    # Shall wait for other lines to come up        
                    else:
                        try:
                            time.sleep(1)                          
                            current_time = timedelta(
                                 hours=datetime.datetime.now().hour, 
                                 minutes=datetime.datetime.now().minute,
                                 seconds=datetime.datetime.now().second)
                            tdelta = current_time - last_scan_time
                            if tdelta.total_seconds() > LOG_WAITING_TIME:
                                f.close()
                                self.terminate()
                                print("Stop scanning process...\n")
                                break
                        except:
                            f.close()
                            self.terminate()
                            raise
          
        except IOError:
            print('\nWARNING: File not Found,'
                + ' please enter another location \n')
            raise
        

class Process:

    """Processes log from scanned lines in the logs queue

    This class has a worker method which is the target of a thread in 
    the Monitor class. This method analyzes the current log in the queue,
    and according to current time, it calls display methods after the end 
    of each HITS_TIME cycle for sections or CHECKING_TIME cycle for alerts
    and statistics.

    Attributes:
        working (bool): Condition in the while loop of the method
        logs (queue.Queue): Queue structure is thread-safe
        sections (dict): Storing sections occurences in a dictionnary
        most_sections (dict): Sections with the most hits
        start_traffic_time (time): Time origin for monitoring traffic
        alert_traffic (int): For traffic counting
        start_section_time (time): Time origin for monitoring section
        count_traffic (int): For reporting traffic while monitoring section
        total_size (int): Total size (bytes) cummulated in an alert cycle
        status (tuple): (1,0,0,0) for successfull request, (0,1,0,0) for 
        redirection, etc...

    """
    
    def __init__(self,logs):
        """ 

        Args:
            logs (qeue.Queue): Is the queue created in the Monitor class

        """
        self.working = True
        self.logs = logs
        self.sections = {}   
        self.most_sections = {}  
        self.start_traffic_time = datetime.datetime.now().time() 
        self.alert_traffic = 0 
        self.start_section_time = datetime.datetime.now().time() 
        self.count_traffic = 0        
        self.total_size = 0
        self.status = (0,0,0,0)


    def terminate(self):
        """ Ends the process of processing, is used in the worker while loop 

        """
        self.working = False
        

    def report(self, count_traffic, start_time, end_time, most_sections):
        """Report on sections with most hits

        Args:
            count_traffic (int): Showing traffic
            start_time (time): Starting time will be converted to str
            end_time (time): Ending time will be converted to str
            section (str): Section which is the most visited
            max_section_hit (int): Showing the number of hits it has

        """
        start_time = start_time.strftime('%H:%M:%S') 
        end_time = end_time.strftime('%H:%M:%S')
        try :
            print("Hits reports: Traffic from " + start_time + " to " + end_time
                 + " :   " + str(count_traffic))
            for section in self.most_sections:
                print("Report: Most visited section: " + section 
                    + " number of hits :" + str(self.most_sections.get(section)))
        except:
            pass


    def display_statistics(self, total_traffic, start_time,
                           end_time, status, size):
        """Informations and statistics every CHECKING_TIME

        If we want to do statistics we need bigger time sample than
        HITS_TIME cycles. Therefore we choose CHECKING_TIME.

        In the common log format, there is just a limited scope of information,
        so this only takes into account time (very important info), status, and
        size.

        Args:
            total_traffic (int): Showing traffic
            start_time (time): Starting time will be converted to str
            end_time (time): Ending time will be converted to str
            statuts (tuple): 
            size (int)

        """      
        start_time = start_time.strftime('%H:%M:%S') 
        end_time = end_time.strftime('%H:%M:%S')
        try:
            pe_s = status[0]/total_traffic*100
            pe_r = status[1]/total_traffic*100
            pe_ce = status[2]/total_traffic*100
            pe_se = status[3]/total_traffic*100
            print("\nInfo: Traffic over the past 2 minutes from " + start_time 
              + " to " + end_time + " - number of hits = " + str(total_traffic))
            print("Statistics: Percentage of successful responses: " + str(pe_s) 
                + '%' 
                + "\n            Percentage of redirections: " + str(pe_r) 
                + '%' 
                + "\n            Percentage of client errors: " + str(pe_ce) 
                + '%'
                + "\n            Percentage of server errors: " + str(pe_se) 
                + '%'
                + "\n            Average size of requests (bytes): " 
                + str(size//total_traffic))

        except :
            pass              

    def display_traffic_alert(self, total_traffic,time):
        """Display alert when traffic every CHECKING_TIME if needed

        Args:
            total_traffic (int): Showing traffic
            time (time): Time will be converted to str

        """     
        time = time.strftime('%H:%M:%S') 
        print("\nALERT: Traffic limit = " + str(TRAFFIC_LIMIT) + "\n")
        print("ALERT: High traffic generated an alert - hits = " 
              + str(total_traffic)+ ", triggered at " + time + "\n") 

    
    def display_traffic_recovered(self, total_traffic,time):
        """Display message when traffic has recovered 

        Args:
            total_traffic (int): Showing traffic
            time (time): Time will be converted to str

        """ 
        time = time.strftime('%H:%M:%S')  
        print("\nRECOVERING: Slowing down" + "\n")  
        print("RECOVERING: Traffic recovered - hits = " + str(total_traffic) 
              + ", recovered at " + time + "\n")
    
    def worker(self):
        """Does the monitoring process, is the target argument of a thread
        in Monitor class.

        It has a while loop that ends when the queue is empty. 
        queue.Queue.get(timeout) method raises an error when the queue is
        empty and has been empty for timeout seconds. Therefore, we 
        choose timeout = LOG_WAITING_TIME. 
        For each loop we get the log at the head of the queue, and can 
        process it, and do statistics,...

        There is a if condition that tests Monitor.simulating. Indeed,
        we can use this program even with non actively written file and
        do statistics previously written samples. 
        After every cycle, start_section_time (for section cycles) and 
        start_alert_time (for alert cycles) become the time the log file 
        has when leaving the time cycle. This choice is also made because
        we do need to keep time tracability.
        But choosing this implies to loose some precision when actively
        reading files. t_section and t_alert are timedelta variables that
        tremendously help in order to gain precision. They enable to keep
        precision in time cycles.

        """       
        alert = False  # becomes True if alert has been displayed

        t_section = timedelta(hours=self.start_section_time.hour, 
                                 minutes=self.start_section_time.minute,
                                 seconds=self.start_section_time.second)
        t_alert = timedelta(hours=self.start_traffic_time.hour,
                                   minutes=self.start_traffic_time.minute,
                                   seconds=self.start_traffic_time.second)
        while self.working:
            try:
                # Gets the head of the queue, see task_done() at the end
                log_str=self.logs.get(timeout=LOG_WAITING_TIME) 
                t_log = timedelta(
                             hours=get_time(log_str).hour,
                             minutes=get_time(log_str).minute,
                             seconds=get_time(log_str).second)
                
                tdelta = t_log - t_section 

                # SECTION CYCLES
                # We will test section cycles before alert cycles
                # SECTION CYCLES

                if abs(tdelta.total_seconds()) > HITS_TIME :
                    # The log is OUT of the current HITS_TIME cycle
                    # End of a cycle

                    self.report(self.count_traffic, self.start_section_time,
                                get_time(log_str), self.most_sections)
 
                        # We have to re-initialize variables, 
                        # at the end of a HITS_TIME cycle
                        
                    self.start_section_time = get_time(log_str)

                    if Monitor.simulating:
                        # Increases precision when actively writting
                        t_section += timedelta(seconds=HITS_TIME)

                    else:
                        # Allows to see on previously written files
                        t_section = timedelta(
                             hours=self.start_section_time.hour, 
                             minutes=self.start_section_time.minute,
                             seconds=self.start_section_time.second)

                    self.count_traffic = 1
                    # Resetting dict, and adding current log
                    self.sections.clear() 
                    self.sections.update({get_section(log_str):1}) 
                    # Resetting dict of most seen, and adding current log
                    self.most_sections.clear() 
                    self.most_sections.update({get_section(log_str):1})


                else:
                    # The log is IN the current HITS_TIME cycle
                    # We should increment variables, dict
                    # section_hit is number of hits to be written 
                    # in the dictionnary, we must create local 
                    # variable otherwise
                    # SyntaxError: can't assign to function call

                    self.count_traffic += 1  
                    if get_section(log_str) in self.sections :
                        section_hit=self.sections.get(get_section(log_str))+1
                    else:
                        section_hit = 1

                    # Incrementing at last the dict
                
                    self.sections.update({get_section(log_str) : section_hit})

                    # Sorting the dictionnary to have most visited sections
                    # after this operation, we have a tuple, for ex :
                    # [('ex6', 0), ('ex5', 1), ('ex1', 2), ('ex3', 3)]

                    sorted_sections = sorted(self.sections.items(),
                                             key=operator.itemgetter(1))
                    try:
                        for i in range(1,NUMBER_SECTIONS+1):
                            self.most_sections.clear() 
                            self.most_sections.update(
                             {sorted_sections[-i][0] : sorted_sections[-i][1]})
                    except:
                        # Errors occuring when traffic is very low
                        self.most_sections.update(
                            {get_section(log_str) : section_hit})


                # ALERT CYCLES
                # Not considering sections with most hits anymore
                # ALERT CYCLES
                      
                tdelta = t_log - t_alert
                
                if abs(tdelta.total_seconds()) > CHECKING_TIME : 
                    # The log is OUT of the current CHECKING_TIME cycle
                
                    self.display_statistics(self.alert_traffic, 
                                                self.start_traffic_time, 
                                                get_time(log_str),
                                                self.status,
                                                self.total_size)
                            
                    if self.alert_traffic > TRAFFIC_LIMIT:
                        self.display_traffic_alert(self.alert_traffic,
                                                   get_time(log_str))
                        alert = True
                    
                    if self.alert_traffic  <  TRAFFIC_LIMIT and alert:
                        self.display_traffic_recovered(self.alert_traffic,
                                                       get_time(log_str))
                        alert = False
                    
                    # We have to re-initialize variables, 
                    # at the end of a CHECKING_TIME cycle
        
                    self.start_traffic_time = get_time(log_str)

                    if Monitor.simulating:
                        # Increases precision when actively writting
                        t_alert += timedelta(seconds=CHECKING_TIME)

                    else:
                        # Allows to see on previously written files
                        t_alert = timedelta(
                               hours=self.start_traffic_time.hour,
                               minutes=self.start_traffic_time.minute,
                               seconds=self.start_traffic_time.second)
                    self.alert_traffic = 1
                    self.total_size = get_size(log_str)
                    self.status = get_status(log_str)

                else:
                    # The log is IN the current CHECKING_TIME cycle
                    # We should increment variables

                    self.alert_traffic += 1
                    self.total_size += get_size(log_str)
                    self.status = tuple(map(operator.add, self.status, get_status(log_str)))
                       
                # Indicates that a formerly enqueued task is complete. 
                # Used by queue consumer threads. 
                # For each get() used to fetch a task, a subsequent call to task_done() 
                # tells the queue that the processing on the task is complete.    

                self.logs.task_done()

            except queue.Empty:
                
                # When timeout = LOG_WAITING_TIME has come to its end
                self.terminate()
                print ('Stop processing... \n')
       
    
class Monitor: 

    """Monitoring the traffic

    This class manages 2 or 3 threads, one for scan and enqueue logs from 
    access log file the other for process and dequeue log one by one.
    It has a method monitoring that launches the threads, and a stop_workers
    method that properly stop all threads, in order to successfully complete
    monitoring by closing properly everything

    Attributes:
        path (str): The path for openning the file
        logs (queue.Queue): Queue structure is thread-safe
        scan (Scan): Scanning part of the monitoring program
        scan_thread (Thread): Thread for scanning, target is scan.worker
        process (Process): Processing part of the monitoring program
        process_thread (Thread): Thread for processing, target is process.worker
        simulating (bool): True if simulating, False if imports a file
        simulator (Simulator): Simulator part of the monitoring program
        simulator_thread (Thread): Thread for simulating, target is simulator.worker

    """

    def __init__(self, path,simulating):
        """ 

        Args:
            path (str): path for opening the file, or the path to create it
            simulating (bool): True if simulating, False if imports a file

        """
        self.path = path 
        self.logs = queue.Queue()
        self.scan = Scan(self.logs, self.path)
        self.scan_thread = threading.Thread(target=self.scan.worker)
        self.process = Process(self.scan.logs)
        self.process_thread = threading.Thread(target=self.process.worker)
        self.simulating = simulating
        self.simulator = Simulator(self.path)
        self.simulator_thread = threading.Thread(target=self.simulator.worker)


    def monitoring(self):  
        """Start scanning and processing logs
        Start the threads activity and then
        wait until the thread terminates. 
    
        """ 
        if self.simulating:
            self.simulator_thread.start()
        self.scan_thread.start()      
        self.process_thread.start()
        self.stop_workers()
    

    def stop_workers(self):
        """Properly stopping all threads

        logs queue is blocked until all items in the queue
        have been gotten and processed.
        Wait until the thread terminates. 
    
        """ 
        
        self.logs.join()
        
        if self.scan_thread != None:
            try:
                self.scan_thread.join()  # Waiting for the thread to finish
            except:
                raise
                print("Interrupted Exception")

        if self.process_thread != None:
            try:
                self.process_thread.join()  # Waiting for the thread to finish
            except:
                raise
                print("Interrupted Exception") 

        if self.simulating:
            if self.simulator_thread != None:
                try:
                    self.simulator_thread.join()
                except:
                    raise
                    print('Thread interrupted')
        # When we come to this point, every thread and every thing
        # has been successfully ended                 
        print("Monitoring successfully completed") 
 

if __name__ =="__main__":
    
    print("\nHTTP traffic monitor\n")
    print("Houssam Zenati")
    simulating = False
    answer=input('Would you like to simulate traffic: yes or no : ')
    while True:
        if answer == 'yes':
            simulating = True
            break
        if answer == 'no':
            break
        else:
            print('Please answer "yes" or "no"')
            answer=input('Would you like to simulate traffic: yes or no : ')

    if simulating:
        path=input('Enter the name of your log file: ')
    else:
        print('Please enter common log format filesystem')
        path=input('Enter the location of your log file: ')
    
    print("Starting Traffic Monitoring")
    Monitor=Monitor(path,simulating)
    Monitor.monitoring()
            