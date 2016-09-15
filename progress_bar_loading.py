import sys
import time
import threading

class progress_bar_loading(threading.Thread):
    
    def run(self):
            global stop
            global kill
            print 'Loading....  ',
            sys.stdout.flush()
            i = 0
            while stop != True:
                    if (i%4) == 0: 
                    	sys.stdout.write('\b/')
                    elif (i%4) == 1: 
                    	sys.stdout.write('\b-')
                    elif (i%4) == 2: 
                    	sys.stdout.write('\b\\')
                    elif (i%4) == 3: 
                    	sys.stdout.write('\b|')

                    sys.stdout.flush()
                    time.sleep(0.2)
                    i+=1
                    
            if kill == True: 
            	print '\b\b\b\b ABORT!',
            else: 
            	print '\b\b done!',
