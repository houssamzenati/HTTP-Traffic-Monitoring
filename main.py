# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 14:59:21 2017

@author: Houssam
"""

import re
import datetime
from datetime import timedelta
import threading
import time
import queue


checking_time= 2*60  #every 2 min
hits_time= 10  #report on most hit section every 1        
traffic_limit=7  #limit for triggering an alert on traffic
read_log_wait_time=5 #time to wait when there is no more line to read in log file
        

        
def getCommonLogFormat(string):
    p = re.compile('([^ ]*) ([^ ]*) ([^ ]*) \[([^]]*)\] "([^"]*)" ([^ ]*) ([^ ]*)')
    m=p.match(string)
    if m is not None:
        ip, rfc_id, user_id, date, request, status, size = m.groups()
        return [ip, rfc_id, user_id, date, request, status, size]
    
def getCommonLogFormatExtended(string):
    p = re.compile(
        '([^ ]*) ([^ ]*) ([^ ]*) \[([^]]*)\] "([^"]*)" ([^ ]*) ([^ ]*)'
        ' "([^"]*)" "([^"]*)"' # extensions
         )
    m=p.match(string)
    ip, rfc_id, user_id, date, 
    request, status, size,
    referer, user_agent = m.groups()
    return ip, rfc_id, user_id, date, request, status, size, referer, user_agent
        
def getSection(string):
    
    section=getCommonLogFormat(string)[4]
    if section!=None and section!='':
        parts = section.split(' ')
        try :
            parts=parts[1] #getting the section
            parts=parts.split('/')
            parts=parts[1:3]
            section='/'.join(parts)
            return section
        except IndexError:
            return None
    else:
        return None
        
        
    """
        if mode=='extended':
            Common_log_format_extended(self)
            section=self.referer
            if self.referer!=None and self.referer!='':
                parts = section.split('/')
                parts=parts[:4] #getting the section
                section='/'.join(parts)
                return section
            else:
                return None
    """
            
def getTime(string):
    
    date=getCommonLogFormat(string)[3]
    parts=date.split(' ')
    parts.remove(parts[-1])
    date=' '.join(parts)
    dt = datetime.datetime.strptime(date, "%d/%b/%Y:%H:%M:%S")
    return dt.time()

def getDay(string):
    
    date=getCommonLogFormat(string)[3]
    parts=date.split(' ')
    parts.remove(parts[-1])
    date=' '.join(parts)
    dt = datetime.datetime.strptime(date, "%d/%b/%Y:%H:%M:%S")
    return dt.day
    
class Scan:
    
    """
     Scans log from an active log file and add it to the queue logs
    """
    def __init__(self,logs):
        self.running = True
        self.logs=logs

    def terminate(self):
        self.running = False
    
    def worker(self):
        try:
            with open(path, 'r') as f:
            #checker certains trucs
                while self.running:
                    line=f.readline()
                    if line != None:
                        try:
                            self.logs.put(line)          
                        except:
                            print("Parsing Error")
                            f.close()
                            Monitor.stop("Invalid log format") #stopping threads
                    else:
                        try:
                            time.sleep(Paramaters.read_log_wait_time) 
                        except:
                            print("Interrupted Exception")
                            f.close()
                            Monitor.stop("Thread interrupted") 
               
        except IOError: 
                Monitor.stop("Log file can not be accessed")
         

    """
     Processes the logs queue in an other thread so that the reading process isn't disturbed
    """
class Process:
    
    def __init__(self,logs):
        self.running = True
        self.sections={} #storing sections occurences
        
        self.startTraffic=datetime.datetime.now().time() #Time origin for monitoring traffic
        self.alertTraffic=0 #traffic count
        
        self.startSection =datetime.datetime.now().time() #Time origin for monitoring section
        self.traffic = 0        #for reporting traffic while monitoring section
        self.section=''   #section with the most hits
        self.maxSectionHit = 0 #biggest number of hits
        self.logs=logs
        
    def terminate(self):
        self.running = False
        
    """
    Report on section with most hits
         
    """
    def report(self, traffic, start, end, section, maxSectionHit):
        
        start=start.strftime('%H:%M:%S') 
        end=end.strftime('%H:%M:%S')
        
        print("INFO: Traffic from "+start+ " to "+ end+" :   "+ str(traffic))
        print("INFO: Most visited section: "+section+ " number of hits :" +str(maxSectionHit))
        

    """
    Message for normal traffic
    """
    def reportNormalTraffic(self, totalTraffic, start, end):
        
        start=start.strftime('%H:%M:%S') 
        end=end.strftime('%H:%M:%S')
        
        print("MESSAGE: Traffic over the pass 2 minutes from "+ start+ " to " 
                  +end + " - number of hits = " + str(totalTraffic))
        


    """
    Show alert when traffic over predefined limit
        
    """
    def showTrafficAlert(self, totalTraffic,date):
        
        date=date.strftime('%H:%M:%S') 
        
        print("ALERT: Traffic limit = " + str(traffic_limit))
        print("ALERT: High traffic generated an alert - hits = "+ str(totalTraffic)+
            ", triggered at " + date)


    """
    Show message that traffic has recovered
         
    """
    def showTrafficRecovered(self, totalTraffic,date):
        date=date.strftime('%H:%M:%S') 
        
        print("MESSAGE: Traffic recovered - hits = "+ str(totalTraffic)+
            ", recovered at " + date)
    
    def worker(self):
        
        alert= False #true if alert has been showing
        log_str=''
        while self.running:
            log_str_before=log_str
            log_str=self.logs.get() # for each loop we get the log at the head of the queue
            
        
            #If the logs queue is not empty, keep analysing until we meet a log that out of time cycle
            if self.logs.empty()==False :
                
                    if type(self.section)==type(None):
                        continue
                    
                    print(log_str_before)
                    try: 
                        t1=timedelta(hours=getTime(log_str).hour,minutes=getTime(log_str).minute,
                                     seconds=getTime(log_str).second)
                        
                        t2=timedelta(hours=self.startSection.hour,minutes=self.startSection.minute,
                                     seconds=self.startSection.second)
                    except TypeError:
                        time.sleep(read_log_wait_time+1)
                        
                    tdelta=t1-t2 
                    #=======monitoring section and common traffic==========
                    if abs(tdelta.total_seconds()) > hits_time:
                        #The log is out of the current cycle
                        Process.report(self, self.traffic, self.startSection, getTime(log_str), self.section, self.maxSectionHit) # end of a cycle, print report
                        
                        #re-initialized variables, including the current log
                        self.startSection = getTime(log_str)
                        self.traffic = 1
                        self.sections.clear()
                        self.sections.update({getSection(log_str):1})
                        self.section = getSection(log_str)
                        self.maxSectionHit=1

                    else:
                        self.traffic +=1 #increment traffic count

                        #increment section hash map
                        # sectionHit number of hits to be written in hash map
                        if getSection(log_str) in self.sections :
                            sectionHit= self.sections.get(getSection(log_str))+1
                        else:
                            sectionHit =1
                        if sectionHit > self.maxSectionHit: 
                            self.maxSectionHit = sectionHit
                            self.section = getSection(log_str)
                        
                        
                    
                        self.sections.update({getSection(log_str):sectionHit})
                    
                    #========counting traffic, check for alert===============
                    
                    t1=timedelta(hours=getTime(log_str).hour,minutes=getTime(log_str).minute,
                                 seconds=getTime(log_str).second)
                    t2=timedelta(hours=self.startTraffic.hour,minutes=self.startTraffic.minute,
                                 seconds=self.startTraffic.second)
                    tdelta=t1-t2
                    
                    if abs(tdelta.total_seconds()) > checking_time: #difference of time in ms
                    
                        Process.reportNormalTraffic(self, self.alertTraffic, self.startTraffic, getTime(log_str))
                        
                        if self.alertTraffic>traffic_limit:
                            Process.showTrafficAlert(self, self.alertTraffic, getTime(log_str))
                            alert = True
                        
                        if self.alertTraffic<traffic_limit and alert:
                            Process.showTrafficRecovered(self,self.alertTraffic, getTime(log_str))
                            alert = False
                        
                        #re-initialized variables, including the current logs
                        self.startTraffic = getTime(log_str)
                        self.alertTraffic =1
                        
                    else:
                        self.alertTraffic+=1
                        
                #If there is no more log to read, check if cycles have terminated and force report
            else :  
                    print('salut')
                    print(log_str_before)
                    print(getDay(log_str_before))
                    if type(self.section)==type(None):
                        #print(log_str)
                        #print(getTime(log_str))
                        print('problem')
                    
                    t1=timedelta(hours=datetime.datetime.now().time().hour,minutes=datetime.datetime.now().time().minute,
                                 seconds=datetime.datetime.now().time().second)
                    t2=timedelta(hours=self.startSection.hour,minutes=self.startSection.minute,
                                 seconds=self.startSection.second)
                    tdelta=t1-t2
                    

                    if tdelta.total_seconds() > hits_time:
                        #Force to report
                        Process.report(self,self.traffic, self.startSection, datetime.datetime.now().time(), self.section, self.maxSectionHit)

                        #re-initialized variables
                        self.startSection = datetime.datetime.now().time()
                        self.traffic = 0;
                        self.sections.clear()
                        self.section = ''
                        self.maxSectionHit = 0;
                        
                    t1=timedelta(hours=datetime.datetime.now().time().hour,minutes=datetime.datetime.now().time().minute,
                                 seconds=datetime.datetime.now().time().second)
                    t2=timedelta(hours=self.startTraffic.hour,minutes=self.startTraffic.minute,
                                 seconds=self.startTraffic.second)
                    tdelta=t1-t2

                    if tdelta.total_seconds() > checking_time:
                        #Force to report
                        Process.reportNormalTraffic(self, self.alertTraffic, self.startTraffic, self.datetime.datetime.now().time())
                    
       

                        if self.alertTraffic>Config.traffic_limit:
                            Process.showTrafficAlert(self,self.alertTraffic, datetime.datetime.now().time())
                            alert = True
                        
                        if self.alertTraffic<Config.traffic_limit and alert:
                            Process.showTrafficRecovered(self,self.alertTraffic, datetime.datetime.now().time())
                            alert = False
                        

                        #re-initializing variables
                        startTraffic = datetime.datetime.now().time()
                        alertTraffic =0
                       
                    
                    #in all case waiting for the reader to add new element
                    try:
                        time.sleep(Config.read_log_time+1) # (interval + 1) assures that the reader has add some elements to  the queue
                    except:
                        print("Interrupted exception")
                        Monitor.stop("Thread Analyse interrupted")
                        
            self.logs.task_done()

        
    
class Monitor:  
    """
 This class manages 2 threads, one for read and enqueue logs from access log file;
 the other for analyse and deque log one by one
 
     """
    def __init__(self):
        self.logs=queue.Queue()
        self.scan=Scan(self.logs)
        self.scanThread=threading.Thread(target=self.scan.worker)
        self.process=Process(self.scan.logs)
        self.processThread=threading.Thread(target=self.process.worker)
    
   
    """
    Start reading and analysing logs
    
    """
    def start(self):      
        self.scanThread.start()      
        self.processThread.start()
        self.logs.join()
        self.scanThread.join()
        self.processThread.join()
        print('Monitoring completed')
    
    """
    Properly stopping all threads
    """
    def stop(self, mes):
        print(mes)
        print("Stop reading process...")
        if self.scanThread!=None:
            self.scan.terminate()
            try:
                self.scanThread.join() #waiting for the thread to finish
            except:
                print("Interrupted Exception")
        if self.processThread!=None:
            self.process.terminate()
            try:
                self.processThread.join() #waiting for the thread to finish
            except:
                print("InterruptedException")   
        print("Reading process stopped")    
   

if __name__ =="__main__":
    
    print("---------------------------------")
    print("|Welcome to HTTP traffic monitor|")
    print("---------------------------------")
    print("Created by Houssam Zenati")
    path=input('Enter the location of your log file: ')
    print("Start Traffic Monitoring")
    Monitor=Monitor()
    Monitor.start()
    
    
    

    

        
        

        