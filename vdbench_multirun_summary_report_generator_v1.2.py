#!/usr/bin/env python
# -*- coding: utf-8 -*-
program_background = """
Created on Tue Apr 04 20:52:45 2017

@author: Srinivas N

Description:
This script finds each and every vdbench log present in the working directory (or directory specified via cmdline)
as well as its child directories and then it processess 'logfile.html' in those vdbench log directories and extracts
some information like vdbench runtime, MBPS [max, min, average, standard deviation] and creates a CSV file which will 
contain the folder path of the found "logfile.html" and its attributes mentioned below.

It will also create a CSV file in each and every vdbench log directory called "summary.csv" which will contain
the above mentioned information but for that particular log only.

Please try --help or -h for more information on 'usage'

"""

import statistics
import fnmatch
import os
import sys
import argparse
from subprocess import PIPE, Popen
import re
import time

version = 'v1.2'

def cmdline(command):
    process = Popen(
        args=command,
        stdout=PIPE,
        shell=True
    )
    return process.communicate()[0]


def extractDataFromFlatFile(fileNameWithAbsolutePath):
    #print fileNameWithAbsolutePath    
    fp = open(fileNameWithAbsolutePath,'r')
    row_number_to_extract = 6 #MB/s row number in this case    
    mylist = []    
    for rows in fp.readlines():
        if rows[0] != '*':
            dataList = rows.split(' ')
            count=0            
            for i in dataList:
                #print i
    
                if i != '' and i != ' ':
                    #print i
                    count = count+1                
                    if count == row_number_to_extract:
                        #print i                    
                        mylist.append(i)
    
    myfloat = []
    
    for i in mylist:
        if i[0].isalpha() is False:
            myfloat.append(float(i))
    
    outputFilePath = fileNameWithAbsolutePath.split('flatfile.html')[0]
    #print outputFilePath    
    output = open(outputFilePath+'summary.csv','w')
    
    #if list is empty means file is present but IOPS data is not there in it
    #could be because the file is empty or it has no MB/s data or something else.
    if not myfloat:
        return str('0,0,0,0,0')
    
    runtimeInSeconds = len(myfloat)
    maxv = max(myfloat)
    minv = min(myfloat)
    mean = statistics.mean(myfloat)
    stddev = statistics.pstdev(myfloat)    
    
    #print "\nmean is "+str(mean)+'\n'
    #print "std dev is "+str(stddev)+'\n'
    
    output.write("Runtime In Seconds,"+str(runtimeInSeconds)+'\n')
    output.write("Max MB/s,"+str(maxv)+'\n')
    output.write("Min MB/s,"+str(minv)+'\n')
    output.write("Mean MB/s,"+str(mean)+'\n')
    output.write("Stddev MB/s,"+str(stddev)+'\n')
    
    output.close()
    fp.close()
    
    return (str(runtimeInSeconds)+','+str(maxv)+','+str(minv)+','+str(mean)+','+str(stddev))
    



def extractDataFromLogFile(fileNameWithAbsolutePath,suppress_summary_file):
    #print fileNameWithAbsolutePath    
    fp = open(fileNameWithAbsolutePath,'r')
    row_number_to_extract = 4 #MB/s row number in this case
    interval_row_number = 2
    mylist = []
    interval = 0
    keepCounting = False
    for rows in fp.readlines():
            dataList = rows.split(' ')
            count=0
            for i in dataList:
                #print i
                if i != '' and i != ' ':
                    #print i
                    count = count+1        
                    if count == interval_row_number:
                        if i.isdigit() and int(i) == 1+interval:
                            keepCounting = True
                            interval = interval+1
                        else:
                            keepCounting = False
                    if keepCounting == True and count == row_number_to_extract:
                        #print i                 
                        mylist.append(i)
    
    myfloat = []
    
    for i in mylist:
        if i[0].isalpha() is False:
            myfloat.append(float(i))
    
    outputFilePath = fileNameWithAbsolutePath.split('logfile.html')[0]
    #print outputFilePath    
    if suppress_summary_file != True:
        output = open(outputFilePath+'summary.csv','w')
    
    #if list is empty means file is present but IOPS data is not there in it
    #could be because the file is empty or it has no MB/s data or something else.
    if not myfloat:
        return str('0,0,0,0,0')
    
    runtimeInSeconds = len(myfloat)
    maxv = max(myfloat)
    minv = min(myfloat)
    mean = statistics.mean(myfloat)
    stddev = statistics.pstdev(myfloat)    
    
    #print "\nmean is "+str(mean)+'\n'
    #print "std dev is "+str(stddev)+'\n'
    
    if suppress_summary_file != True:
        output.write("Runtime In Seconds,"+str(runtimeInSeconds)+'\n')
        output.write("Max MB/s,"+str(maxv)+'\n')
        output.write("Min MB/s,"+str(minv)+'\n')
        output.write("Mean MB/s,"+str(mean)+'\n')
        output.write("Stddev MB/s,"+str(stddev)+'\n')
        
        output.close()

    fp.close()
    
    return (str(runtimeInSeconds)+','+str(maxv)+','+str(minv)+','+str(mean)+','+str(stddev))
    





def getVdbenchParameters(fileNameWithAbsolutePath):

    lun = ''
    parameter = ''    

    #filename = fileNameWithAbsolutePath.split('logfile.html')[0]+'\\parmscan.html'    
    filename = fileNameWithAbsolutePath.split('logfile.html')[0]+'\\parmfile.html'    
    #filename = fileNameWithAbsolutePath    
    
    try:    
        fp = open(filename,'r')
    except Exception as e:
        #print 'Unable to access parmfile.html'
        #print str(e)
        return 'file_not_found/accessible,file_not_found/accessible'
        
        
    dataBuffer = fp.read()
    fp.close()
    #i found that scanning parmscan.html is not a good idea because it was written only when
    #vdbench was terminated properly but when abruptly power was cut it was not written at all.
    # so now we will search from parmfile.html instead
    '''
    #for parmscan.html    
    if dataBuffer.find('keyw: lun=') != -1:
        lun = dataBuffer.split('keyw: lun=')[1].split('\n')[0]
    else:
        lun = 'NA'
    
    if dataBuffer.find('keyw: seekpct=') != -1:
        seekpct = dataBuffer.split('keyw: seekpct=')[1].split('\n')[0]
    else:
        seekpct = 'NA'
        
    if dataBuffer.find('keyw: xfersize=') != -1:
        xfersize = dataBuffer.split('keyw: xfersize=')[1].split('\n')[0]
    else:
        xfersize = 'NA'
        
    if dataBuffer.find('keyw: rdpct=') != -1:
        rdpct = dataBuffer.split('keyw: rdpct=')[1].split('\n')[0]
    else:
        rdpct = 'NA'
        
    if dataBuffer.find('keyw: threads=') != -1:
        threads = dataBuffer.split('keyw: threads=')[1].split('\n')[0]
    else:
        threads = 'NA'

    if seekpct.lower() == 'sequential':
        parameter = 'S'
    elif seekpct.lower()  == 'random':
        parameter = 'R'
    else:
        parameter = 'NA' #error undefined Parameter
    '''

    #for parmfile.html
    if dataBuffer.find('lun=') != -1:
        lun = dataBuffer.split('lun=')[1]
        lun = re.split(',|\n',lun)[0]
        lun = lun.strip(' ')
    else:
        lun = 'NA'
    
    if dataBuffer.find('seekpct=') != -1:
        seekpct = dataBuffer.split('seekpct=')[1]
        seekpct = re.split(',|\n',seekpct)[0]
        seekpct = seekpct.strip(' ')
    else:
        seekpct = 'NA'
        
    if dataBuffer.find('xfersize=') != -1:
        xfersize = dataBuffer.split('xfersize=')[1]
        xfersize = re.split(',|\n',xfersize)[0]
        xfersize = xfersize.strip(' ')
    else:
        xfersize = 'NA'
        
    if dataBuffer.find('rdpct=') != -1:
        rdpct = dataBuffer.split('rdpct=')[1].split(',')[0].strip(' ')
        rdpct = re.split(',|\n',rdpct)[0]
        rdpct = rdpct.strip(' ')
    else:
        rdpct = 'NA'
        
    if dataBuffer.find('threads=') != -1:
        threads = dataBuffer.split('threads=')[1]
        threads = re.split(',|\n',threads)[0]
        threads = threads.strip(' ')
    else:
        threads = 'NA'

    if seekpct.lower() == 'sequential' or seekpct.lower() == '0':
        parameter = 'S'
    elif seekpct.lower()  == 'random' or seekpct.lower() == '100':
        parameter = 'R'
    else:
        parameter = 'NA' #error undefined Parameter    
    
    parameter = parameter+xfersize.upper()+rdpct+'R'+'_'+threads+'QD'
    return lun+','+parameter



#------------------------------------------main program----------------------------------------------------


try:
    
    #we can later add an option if required to take filename input from user at starting.    
    resultFileName = 'result.csv'

    current_dir = cmdline('cd')
    current_dir = current_dir[:-2]# i don't why but sometimes it just adds to new lines at end so had to remove them    
    
    root_dir = './'
    
    suppress_local_summary = False    
    
    
    parser = argparse.ArgumentParser(description='Vdbench_multiple_log_summary_report_generator '+version+' by Srinivas N\n')
    parser.add_argument('-p','--analysis-dir', help='Specify the Directory path to search for vdbench logs, default is current directory', default='./',required=False)
    parser.add_argument('-o','--output-file', help="Specify filename and path for Result file, default is 'result.csv' file in current directory", default='./result.csv',required=False)
    parser.add_argument('-s','--suppress-local-summary',action='store_true', help='Suppress generation of summary sheet in each vdbench log folder', required=False)
    parser.add_argument('-v','--program-history',action='store_true', help='Print program detailed description and version history', required=False)    
    
    args = vars(parser.parse_args())
    #it works but findout how to customise help message show that we can include history


    if args['program_history'] == True:
        print program_background
        #exit(0) is only defined for the interpreter not for compiled executable
        sys.exit(0)
        
    if args['suppress_local_summary'] == True:
        suppress_local_summary = True
        
    #print 'input directory argument is '+str(args)
    root_dir = args['analysis_dir']
    
    resultFileName = args['output_file']
    
    

    
    #print 'analysis dir is '+root_dir

    #print 'current_dir is '+current_dir    
    
    sys.stdout.write('Vdbench_multiple_log_summary_report_generator '+version+' by Srinivas N\n')
    sys.stdout.write('Please wait Processing...')
    
    #scan dir and generate report
    
    
    
    fresult = open(resultFileName,'w+')
    fresult.write('Vdbench Multiple Log Summary Generator '+version+' Report File\n')
    fresult.write('Report Generation Time:,'+time.strftime('%Y-%m-%d %H:%M:%S')+'\n')
    if root_dir == './':
        fresult.write('Analysis Directory:,'+current_dir+'\n')
    else:
        fresult.write('Analysis Directory:,'+root_dir+'\n')
    fresult.write('Serial Num, Sub-directory (vdbench log file paths), Device Name (LUN), Vdbench Parameters, Runtime (s),Max (MB/s),Min (MB/s),Average (MB/s),Standard Deviation (MB/s)\n')
    
    fileName_to_search = 'logfile.html'
    
    
    matches = []
    
    #had to use sys.stdout.write because print() by default sends the next print() call to
    #newline, and there are someways to avoid it like either placing comma after the string (which will give a whitespace)
    #or from __future__ print_function (only for python 2.6+) which will make print() behave as python 3.x print() and then we can use 
    # print(data,end=''), but I didn't want any special dependencies so I decided to got with sys.stdout.write().
    
    serialNumer = 0
    #search current directory for the file
    for root, dirnames, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, fileName_to_search):
            
            #test
            #print 'root '+str(root)+'\n'        
            #print 'dirnames '+str(dirnames)+'\n'
            #print 'filename '+str(filename)+'\n'
            
            #if we give comma after print then next print statement won't go to newline        
            #print '.',        
            sys.stdout.write('.')        
            
            foundFileName = os.path.join(root, filename)
            outputData = extractDataFromLogFile(foundFileName,suppress_local_summary)
            parameterData = getVdbenchParameters(foundFileName)            
            
            splittedFileName = foundFileName.split(fileName_to_search)[0]
            
            #after implementing this subdirectory thing I felt like the real usefulness lies in 
            #providing the full path name because then I can straightaway copy that path paste in
            #explorer and see that data rather than doing that merging of parent and sub paths etc
            #splittedFileName = splittedFileName.split(root_dir)[1]
            
            if root_dir == './':
                path_name = current_dir +'\\' + splittedFileName.split('./')[1]
            else:
                path_name = splittedFileName
            
            serialNumer = serialNumer+1
          
            fresult.write(str(serialNumer)+','+path_name+','+parameterData+','+outputData+'\n')
            matches.append(foundFileName)
            
    #print matches
    
    if not matches:
        #print fileName_to_search +' found'
        sys.stdout.write('\n'+fileName_to_search +' not found')
        sys.stdout.write('\nPress any key to exit.')
    else:
        sys.stdout.write('\nDone, Output in \"'+ resultFileName + '\"\nPress any key to exit.')
    #print '\npress any key to exit'
    
    fresult.close()

    raw_input()
        
    

except Exception as e:
    sys.stdout.write('\nError occurred, Please find the Error details below:\n')
    sys.stdout.write(str(e))
    sys.stdout.write('\nPress any key to exit.')
    raw_input()
    
