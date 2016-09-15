import threading
import os
import shutil
import glob
import time
import cdb
import sys
import dbtools
import subprocess
import winsound
import pickle
import hashlib #instead of md5
from subprocess import Popen, PIPE

class progress_bar_loading(threading.Thread):
    
    def run(self):
            global stop
            global kill
            print 'Loading...',
            sys.stdout.flush()
            i = 0
            while stop != True:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                    time.sleep(0.7)
                    i+=1
                    
            if kill == True: 
            	print '....ABORT!',
            else: 
            	print '..Done!',


"""
Threaded Jobs.

Any class that does a long running process can inherit
from ThreadedJob.  This enables running as a background
thread, progress notification, pause and cancel.  The
time remaining is also calculated by the ThreadedJob class.
"""
import wx.lib.newevent
import thread
import exceptions
import time

(RunEvent, EVT_RUN) = wx.lib.newevent.NewEvent()
(CancelEvent, EVT_CANCEL) = wx.lib.newevent.NewEvent()
(DoneEvent, EVT_DONE) = wx.lib.newevent.NewEvent()
(ProgressStartEvent, EVT_PROGRESS_START) = wx.lib.newevent.NewEvent()
(ProgressEvent, EVT_PROGRESS) = wx.lib.newevent.NewEvent()

class InterruptedException(exceptions.Exception):
    def __init__(self, args = None):
        self.args = args
    #
#

class ThreadedJob:
    def __init__(self):
        # tell them ten seconds at first
        self.secondsRemaining = 10.0
        self.lastTick = 0

        # not running yet
        self.isPaused = False
        self.isRunning = False
        self.keepGoing = True

    def Start(self):
        self.keepGoing = self.isRunning = True
        thread.start_new_thread(self.Run, ())

        self.isPaused = False
    #

    def Stop(self):
        self.keepGoing = False
    #

    def WaitUntilStopped(self):
        while self.isRunning:
            time.sleep(0.1)
            wx.SafeYield()
        #
    #

    def IsRunning(self):
        return self.isRunning
    #

    def Run(self):
        # this is overridden by the
        # concrete ThreadedJob
        print "Run was not overloaded"
        self.JobFinished()

        pass
    #

    def Pause(self):
        self.isPaused = True
        pass
    #

    def Continue(self):
        self.isPaused = False
        pass
    #

    def PossibleStoppingPoint(self):
        if not self.keepGoing:
            raise InterruptedException("process interrupted.")
        wx.SafeYield()

        # allow cancel while paused
        while self.isPaused:
            if not self.keepGoing:
                raise InterruptedException("process interrupted.")

            # don't hog the CPU
            time.sleep(0.1)
        #
    #

    def SetProgressMessageWindow(self, win):
        self.win = win
    #

    def JobBeginning(self, totalTicks):

        self.lastIterationTime = time.time()
        self.totalTicks = totalTicks

        if hasattr(self, "win") and self.win:
            wx.PostEvent(self.win, ProgressStartEvent(total=totalTicks))
        #
    #

    def JobProgress(self, currentTick):
        dt = time.time() - self.lastIterationTime
        self.lastIterationTime = time.time()
        dtick = currentTick - self.lastTick
        self.lastTick = currentTick

        alpha = 0.92
        if currentTick > 1:
            self.secondsPerTick = dt * (1.0 - alpha) + (self.secondsPerTick * alpha)
        else:
            self.secondsPerTick = dt
        #

        if dtick > 0:
            self.secondsPerTick /= dtick

        self.secondsRemaining = self.secondsPerTick * (self.totalTicks - 1 - currentTick) + 1

        if hasattr(self, "win") and self.win:
            wx.PostEvent(self.win, ProgressEvent(count=currentTick))
        #
    #

    def SecondsRemaining(self):
        return self.secondsRemaining
    #

    def TimeRemaining(self):

        if 1: #self.secondsRemaining > 3:
            minutes = self.secondsRemaining // 60
            seconds = int(self.secondsRemaining % 60.0)
            return "%i:%02i" % (minutes, seconds)
        else:
            return "a few"
    #

    def JobFinished(self):
        if hasattr(self, "win") and self.win:
            wx.PostEvent(self.win, DoneEvent())
        #

        # flag we're done before we post the all done message
        self.isRunning = False
    #
#

class EggTimerJob(ThreadedJob):
    """ A sample Job that demonstrates the mechanisms and features of the Threaded Job"""
    def __init__(self, duration):
        self.duration = duration
        ThreadedJob.__init__(self)
    #

    def Run(self):
        """ This can either be run directly for synchronous use of the job,
        or started as a thread when ThreadedJob.Start() is called.

        It is responsible for calling JobBeginning, JobProgress, and JobFinished.
        And as often as possible, calling PossibleStoppingPoint() which will 
        sleep if the user pauses, and raise an exception if the user cancels.
        """
        self.time0 = time.clock()
        self.JobBeginning(self.duration)

        try:
            for count in range(0, self.duration):
                time.sleep(1.0)
                self.JobProgress(count)
                self.PossibleStoppingPoint()
            #
        except InterruptedException:
            # clean up if user stops the Job early
            print "canceled prematurely!"
        #

        # always signal the end of the job
        self.JobFinished()
        #
    #

    def __str__(self):
        """ The job progress dialog expects the job to describe its current state."""
        response = []
        if self.isPaused:
            response.append("Paused Counting")
        elif not self.isRunning:
            response.append("Will Count the seconds")
        else:
            response.append("Counting")
        #
        return " ".join(response)
    #
#

class FileCopyJob(ThreadedJob):
    """ A common file copy Job. """

    def __init__(self, orig_filename, copy_filename, block_size=32*1024):

        self.src = orig_filename
        self.dest = copy_filename
        self.block_size = block_size
        ThreadedJob.__init__(self)
    #

    def Run(self):
        """ This can either be run directly for synchronous use of the job,
        or started as a thread when ThreadedJob.Start() is called.

        It is responsible for calling JobBeginning, JobProgress, and JobFinished.
        And as often as possible, calling PossibleStoppingPoint() which will 
        sleep if the user pauses, and raise an exception if the user cancels.
        """
        self.time0 = time.clock()

        try:
            source = open(self.src, 'rb')

            # how many blocks?
            import os
            (st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime) = os.stat(self.src)
            num_blocks = st_size / self.block_size
            current_block = 0

            self.JobBeginning(num_blocks)

            dest = open(self.dest, 'wb')

            while 1:
                copy_buffer = source.read(self.block_size)
                if copy_buffer:
                    dest.write(copy_buffer)
                    current_block += 1
                    self.JobProgress(current_block)
                    self.PossibleStoppingPoint()
                else:
                    break

            source.close()
            dest.close()

        except InterruptedException:
            # clean up if user stops the Job early
            dest.close()
            # unlink / delete the file that is partially copied
            os.unlink(self.dest)
            print "canceled, dest deleted!"
        #

        # always signal the end of the job
        self.JobFinished()
        #
    #

    def __str__(self):
        """ The job progress dialog expects the job to describe its current state."""
        response = []
        if self.isPaused:
            response.append("Paused Copy")
        elif not self.isRunning:
            response.append("Will Copy a file")
        else:
            response.append("Copying")
        #
        return " ".join(response)
    #
#

class JobProgress(wx.Dialog):
    """ This dialog shows the progress of any ThreadedJob.

    It can be shown Modally if the main application needs to suspend
    operation, or it can be shown Modelessly for background progress
    reporting.

    app = wx.PySimpleApp()
    job = EggTimerJob(duration = 10)
    dlg = JobProgress(None, job)
    job.SetProgressMessageWindow(dlg)
    job.Start()
    dlg.ShowModal()


    """
    def __init__(self, parent, job):
        self.job = job

        wx.Dialog.__init__(self, parent, -1, "Progress", size=(350,200), style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)


        # vertical box sizer
        sizeAll = wx.BoxSizer(wx.VERTICAL)

        # Job status text
        self.JobStatusText = wx.StaticText(self, -1, "Starting...")
        sizeAll.Add(self.JobStatusText, 0, wx.EXPAND|wx.ALL, 8)

        # wxGague
        self.ProgressBar = wx.Gauge(self, -1, 10, wx.DefaultPosition, (250, 15))
        sizeAll.Add(self.ProgressBar, 0, wx.EXPAND|wx.ALL, 8)

        # horiz box sizer, and spacer to right-justify
        sizeRemaining = wx.BoxSizer(wx.HORIZONTAL)
        sizeRemaining.Add((2,2), 1, wx.EXPAND)

        # time remaining read-only edit
        # putting wide default text gets a reasonable initial layout.
        self.remainingText = wx.StaticText(self, -1, "???:??")
        sizeRemaining.Add(self.remainingText, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 8)

        # static text: remaining
        self.remainingLabel = wx.StaticText(self, -1, "remaining")
        sizeRemaining.Add(self.remainingLabel, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 8)

        # add that row to the mix
        sizeAll.Add(sizeRemaining, 1, wx.EXPAND)

        # horiz box sizer & spacer
        sizeButtons = wx.BoxSizer(wx.HORIZONTAL)
        sizeButtons.Add((2,2), 1, wx.EXPAND|wx.ADJUST_MINSIZE)

        # Pause Button
        self.PauseButton = wx.Button(self, -1, "Pause")
        sizeButtons.Add(self.PauseButton, 0, wx.ALL, 4)
        self.Bind(wx.EVT_BUTTON, self.OnPauseButton, self.PauseButton)

        # Cancel button
        self.CancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        sizeButtons.Add(self.CancelButton, 0, wx.ALL, 4)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.CancelButton)

        # Add all the buttons on the bottom row to the dialog
        sizeAll.Add(sizeButtons, 0, wx.EXPAND|wx.ALL, 4)

        self.SetSizer(sizeAll)
        #sizeAll.Fit(self)
        sizeAll.SetSizeHints(self)

        # jobs tell us how they are doing
        self.Bind(EVT_PROGRESS_START, self.OnProgressStart)
        self.Bind(EVT_PROGRESS, self.OnProgress)
        self.Bind(EVT_DONE, self.OnDone)

        self.Layout()
    #

    def OnPauseButton(self, event):
        if self.job.isPaused:
            self.job.Continue()
            self.PauseButton.SetLabel("Pause")
            self.Layout()
        else:
            self.job.Pause()
            self.PauseButton.SetLabel("Resume")
            self.Layout()
        #
    #

    def OnCancel(self, event):
        self.job.Stop()
    #

    def OnProgressStart(self, event):
        self.ProgressBar.SetRange(event.total)
        self.statusUpdateTime = time.clock()
    #

    def OnProgress(self, event):
        # update the progress bar
        self.ProgressBar.SetValue(event.count)

        self.remainingText.SetLabel(self.job.TimeRemaining())

        # update the text a max of 20 times a second
        if time.clock() - self.statusUpdateTime > 0.05:
            self.JobStatusText.SetLabel(str(self.job))
            self.statusUpdateTime = time.clock()
            self.Layout()
        #
    #

    # when a job is done
    def OnDone(self, event):
        self.ProgressBar.SetValue(0)
        self.JobStatusText.SetLabel("Finished")
        self.Destroy()
    #
#



SCANNED_DOCUMENTS_FOLDER_LOCATION = "T:\\reception 1\\"
OUTPUT_DOCUMENTS_FOLDER_LOCATION = "F:\\Patient Scans\\Patient Scans\\"
SOUND_FILENAME = "F:\\Patient Scans\\beep-08b.mp3"

DEBUG = False
ASK_TO_SYNC = False
ASK_TO_CONTINUE = False
PLAY_SOUND = False
COMPLETION_PROMPTS = False
ONE_FILE_MODE = True # True automatically waits for the first file and retrieves it # False does not
PROGRESS_BAR = False

db = cdb
db.check_db()

def info(message):
    print "[INFO] " + str(message)

def warning(message):
    print "[WARNING] " + str(message)

def critical(message):
    print "[CRITICAL] " + str(message)

def error(message):
    print "[ERROR] " + str(message)

def fileio(message):
    print "[FILE I/O] " + str(message)

def debug(message):
    if DEBUG:
        print "[DEBUG] " + str(message)

def success(message):
    if COMPLETION_PROMPTS:
        print "[SUCCESS] " + str(message)

def checkPath(path):
    return os.path.exists(path)

def getFiles(mypath):
    try:
        onlyfiles = [ f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath,f)) ]
    except WindowsError:
        time.sleep(2)
        getFiles(mypath)
    return onlyfiles

def isFolderFilled(path):
    return len(getFiles(path)) > 0

def moveFiles(source_dir, dest_dir): # OLD METHOD TO COPY
    for filename in glob.glob(os.path.join(source_dir, '*.*')):
        fileio("File '" + filename + "' copying!")
        start_time = time.time()
        shutil.copy(filename, dest_dir)
        #debug(str(time.time() - start_time) + " seconds")

def moveFiles2(source_dir, dest_dir): # FASTER & MORE EFFICIENT COPY
    for filename in glob.glob(os.path.join(source_dir, '*.*')):
        fileio("File '" + filename + "' copying to directory: '" + os.path.basename(dest_dir) + "'!")
        start_time = time.time()
        copyFile2(os.path.join(source_dir,filename), os.path.join(dest_dir, os.path.basename(filename)))
        #debug(str(time.time() - start_time) + " seconds")

def copyFile2(src, dst, buffer_size=10485760, perserveFileDate=True):
    app = wx.App(False)
    #job = EggTimerJob(duration = 10)
    job = FileCopyJob(src, dst, buffer_size)
    dlg = JobProgress(None, job)
    job.SetProgressMessageWindow(dlg)
    job.Start()
    dlg.ShowModal()

def copyFile(src, dst, buffer_size=10485760, perserveFileDate=True): 
    '''
    Copies a file to a new location. Much faster performance than Apache Commons due to use of larger buffer
    @param src:    Source File
    @param dst:    Destination File (not file path)
    @param buffer_size:    Buffer size to use during copy
    @param perserveFileDate:    Preserve the original file date
    '''
    global stop
    global kill
    #    Check to make sure destination directory exists. If it doesn't create the directory
    dstParent, dstFileName = os.path.split(dst)
    if(not(os.path.exists(dstParent))):
        os.makedirs(dstParent)

    #    Make sure the file finished copying first before copying over
    if not checkAllFilesForChanges(SCANNED_DOCUMENTS_FOLDER_LOCATION):
        warning("File Changes UNCONFIRMED!")
        waitForChangeCompletion(SCANNED_DOCUMENTS_FOLDER_LOCATION)
    
    #    Optimize the buffer for small files
    buffer_size = min(buffer_size,os.path.getsize(src))
    if(buffer_size == 0):
        buffer_size = 1024
    
    if shutil._samefile(src, dst):
        raise shutil.Error("`%s` and `%s` are the same file" % (src, dst))
    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if shutil.stat.S_ISFIFO(st.st_mode):
                raise shutil.SpecialFileError("`%s` is a named pipe" % fn)

    #    Initialize copy progress bar
    if PROGRESS_BAR:
        kill = False      
        stop = False
        p = progress_bar_loading()
        p.start()

    try:
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                shutil.copyfileobj(fsrc, fdst, buffer_size)
                
        if(perserveFileDate):
            shutil.copystat(src, dst)
        stop = True
    except KeyboardInterrupt or EOFError:
         kill = True
         stop = True

    


def removeFilesInDirectory(path):
    for root, dirs, files in os.walk(path):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except:
                retry2 = raw_input(error("Unable to delete file: %s! Retry? (y) " % str(name)))
                if ('n' or 'N') in retry2:
                    return False
                    continue
                else:
                    time.sleep(1)
                    os.remove(os.path.join(root, name))
        return True
                
def representsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False                

def promptInformation():
    while True:
        dataset = {}
        print "============================================="
        print "===== What would you like to search by? ====="
        print "=====                                   ====="
        print "===== 1. Last Name                      ====="
        print "===== 2. First Name                     ====="
        print "===== 3. Middle Name                    ====="
        print "===== 4. Date of Birth                  ====="
        print "===== 5. SyncToy Sync                   ====="
        print "===== 6. Quit                           ====="
        print "============================================="
        sType = raw_input("\nSearch By: (1) ")
        if not representsInt(sType):
            sType = "1"
        sType = int(sType)
        print "\n"
        if sType == 1:
            dataset['last_name'] = raw_input("Last name: ")
        elif sType == 2:
            dataset['first_name'] = raw_input("First name: ")
        elif sType == 3:
            dataset['middle_name'] = raw_input("Middle name: ")
        elif sType == 4:
            dataset['dob'] = raw_input("Date of Birth (XX/YY/ZZZZ): ")
        elif sType == 5:
            runSyncToy()
            continue
        elif sType == 6:
            sys.exit(0)
        print "\n############# CHOOSE AN ENTRY #############"
        count = 0
        if sType == 1:
            for entry in dbtools.csv_find(dataset['last_name']):
                print str(count + 1) + ". " + entry['first_name'] + " " + entry['last_name'] + " " + entry['middle_name'] + " " + entry['dob']
                count+=1
        elif sType == 2:
            for entry in dbtools.csv_find('',dataset['first_name']):
                print str(count + 1) + ". " + entry['first_name'] + " " + entry['last_name'] + " " + entry['middle_name'] + " " + entry['dob']
                count+=1
        elif sType == 3:
            for entry in dbtools.csv_find('','',dataset['middle_name']):
                print str(count + 1) + ". " + entry['first_name'] + " " + entry['last_name'] + " " + entry['middle_name'] + " " + entry['dob']
                count+=1
        elif sType == 4:
            for entry in dbtools.csv_find('','','',dataset['dob']):
                print str(count + 1) + ". " + entry['first_name'] + " " + entry['last_name'] + " " + entry['middle_name'] + " " + entry['dob']
                count+=1
        print str(count + 1) + ". Other/Manual Entry"
        count+=1
        print str(count + 1) + ". Retry?"
        print "###########################################\n"
        entry_value = int(raw_input("[PROMPT] Patient Number? ")) - 1
        if count - 1 == entry_value: # If manual entry is selected
            dataset['last_name'] = raw_input("Last name: ")
            dataset['first_name'] = raw_input("First name: ")
            dataset['middle_name'] = raw_input("Middle name: ")
            dataset['dob'] = raw_input("Date of Birth (XX-YY-ZZZZ): ")
            break
        elif entry_value != count:
            if sType == 1:
                entry = dbtools.csv_find(dataset['last_name'])[entry_value]
            elif sType == 2:
                entry = dbtools.csv_find('',dataset['first_name'])[entry_value]
            elif sType == 3:
                entry = dbtools.csv_find('','',dataset['middle_name'])[entry_value]
            elif sType == 4:
                entry = dbtools.csv_find('','','',dataset['dob'])[entry_value]
            dataset = entry
            dataset['dob'] = dataset['dob'].replace("/", "-")
            break
        elif count == entry_value: # If retry is selected
            print '\n'
            continue
    db_box_id = db.read_db()['box_id']
    user_box_id = raw_input(("Box ID (Last Used - %s): " % db_box_id))
    if user_box_id is '':
        dataset['box_id'] = db_box_id
    else:
        dataset['box_id'] = user_box_id
        db.update_db({'box_id':user_box_id})
    return dataset

def promptInformation2():
    while True:
        dataset = {}
        patient_set = {}
        print "============================================="
        print "===== What would you like to search by? ====="
        print "=====                                   ====="
        print "===== 1. Keyword Search                 ====="
        print "===== 2. SyncToy Sync                   ====="
        print "===== 3. Quit                           ====="
        print "============================================="
        sType = raw_input("\nSearch By: (1) ")
        print "\n"
        if not representsInt(sType):
            sType = "1"
        sType = int(sType)
        if sType == 2:
            runSyncToy()
            continue
        elif sType == 3:
            sys.exit(0)
        search_term = raw_input("Search By: ")
        print "\n############# CHOOSE AN ENTRY #############"
        count = 0
        for entry in dbtools.csv_find(search_term):
            printData(count, entry)
            patient_set = saveData(count, entry, patient_set)
            count+=1
        for entry in dbtools.csv_find('',search_term):
            printData(count, entry)
            patient_set = saveData(count, entry, patient_set)
            count+=1
        for entry in dbtools.csv_find('','',search_term):
            printData(count, entry)
            patient_set = saveData(count, entry, patient_set)
            count+=1
        for entry in dbtools.csv_find('','','',search_term):
            printData(count, entry)
            patient_set = saveData(count, entry, patient_set)
            count+=1
        print str(count + 1) + ". Other/Manual Entry"
        count+=1
        print str(count + 1) + ". Retry?"
        print "###########################################\n"

        entry_value = ""
        try:
            entry_value = int(raw_input("Patient Number? ")) - 1
        except ValueError:
            while not str(entry_value).isdigit():
                try:
                    entry_value = int(raw_input("Patient Number? ")) - 1
                except:
                    continue
                
        if count == entry_value: # If retry is selected
            print '\n'
            continue
        elif count - 1 == entry_value: # If manual entry is selected
            dataset['last_name'] = raw_input("Last name: ")
            dataset['first_name'] = raw_input("First name: ")
            dataset['middle_name'] = raw_input("Middle name: ")
            dataset['dob'] = raw_input("Date of Birth (XX-YY-ZZZZ): ")
        elif entry_value != count: # If patient is selected
            dataset = patient_set[entry_value]
            dataset['dob'] = dataset['dob'].replace("/", "-")

        ### Retrieve Box ID Number from Database ###
        db_box_id = db.read_db()['box_id']
        user_box_id = raw_input(("Box ID (Last Used - %s): " % db_box_id))
        if user_box_id is '':
            dataset['box_id'] = db_box_id
        else:
            dataset['box_id'] = user_box_id
            db.update_db({'box_id':user_box_id})
        return dataset

def printData(count, entry):
    print str(count + 1) + ". " + entry['first_name'] + " " + entry['last_name'] + " " + entry['middle_name'] + " " + entry['dob']

def saveData(count, entry, patient_set):
    patient_set[count] = entry
    return patient_set

def promptFileConfirmation(dataset):
    string = raw_input("[PROMPT] Confirm patient: %s, %s? (y) " % (dataset['last_name'], dataset['first_name']))
    return not ('n' or 'N') in string

def getFileSize(path):
    f = open(path, "rb")
    old_file_position = f.tell()
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(old_file_position, os.SEEK_SET)
    f.close()
    return size

def isFileChange(path):
    size_0 = getFileSize(path)
    time.sleep(0.5) # Wait 0.5 seconds before checking file size again #
    size_1 = getFileSize(path)
    debug("File: %s, Size 1: %d, Size 2: %d, Diff: %d" % (path, size_0, size_1, size_1 - size_0))
    if size_0 == size_1:
        return False
    return True

def isFileChange2(path):
    modTime1 = os.path.getmtime(path)
    time.sleep(0.5) # Wait 0.5 seconds before checking if modified #
    modTime2 = os.path.getmtime(path)
    if modTime1 == modTime2:
        return False
    return True

def filehash(filepath, blocksize=4096):
    """ Return the hash hexdigest for the file `filepath', processing the file
    by chunk of `blocksize'.

    :type filepath: str
    :param filepath: Path to file

    :type blocksize: int
    :param blocksize: Size of the chunk when processing the file

    """
    sha = hashlib.sha256()
    with open(filepath, 'rb') as fp:
        while 1:
            data = fp.read(blocksize)
            if data:
                sha.update(data)
            else:
                break
    return sha.hexdigest()

def isFileChange3(path):
    file_hash_1 = filehash(path)
    time.sleep(0.1)
    file_hash_2 = filehash(path)
    if file_hash_1 == file_hash_2:
        return False
    return True

def checkAllFilesForChanges(directory): # Check if Able to Proceed to Copy Phase # False = NOT able to proceed, changes still occuring # True = All Okay
    for fi in getFiles(directory):
        #if isFileChange3(directory + '\\' + fi):
        #    debug("File Change on HASH Pass 0 Failed!")
        #    return False
        for x in range(0, 9):
            if isFileChange2(directory + '\\' + fi):
                debug("File Change on MTime Pass %d Failed!" % x)
                return False
            elif isFileChange(directory + '\\' + fi):
                debug("File Change on Size Pass %d Failed!" % x)
                return False

    return True

def waitForChangeCompletion(directory):
    info("File Changes Confirmed! Waiting for completion...")
    while True:
        if checkAllFilesForChanges(directory):
            success("File Changes Completed!")
            break

def runSyncToy():
    subprocess.call(["C:\Program Files\SyncToy 2.1\SyncToyCmd.exe", "-R"])

def beep(sound):
    winsound.PlaySound('%s.wav' % sound, winsound.SND_FILENAME)

if __name__ == "__main__":
    while True:
        if not checkPath(SCANNED_DOCUMENTS_FOLDER_LOCATION):
            critical("Scanned Document Location NOT available! Please connect drive!")
            break
        dataset = promptInformation2()
        if promptFileConfirmation(dataset):
            while True:
                if (isFolderFilled(SCANNED_DOCUMENTS_FOLDER_LOCATION)):
                    OUTPUT_DIR = OUTPUT_DOCUMENTS_FOLDER_LOCATION + "\\" + "Box " + "- " + dataset['box_id'] + "\\" + dataset['last_name'] + ", " + dataset['first_name'] + " " + dataset['middle_name'] + " _ " + dataset['dob']
                    if not checkAllFilesForChanges(SCANNED_DOCUMENTS_FOLDER_LOCATION):
                        waitForChangeCompletion(SCANNED_DOCUMENTS_FOLDER_LOCATION)
                    if not os.path.exists(OUTPUT_DIR):
                        os.makedirs(OUTPUT_DIR)
                        success("Directory successfully created!")
                    moveFiles2(SCANNED_DOCUMENTS_FOLDER_LOCATION, OUTPUT_DIR)
                    success("All files have been successfully copied!")
                    if removeFilesInDirectory(SCANNED_DOCUMENTS_FOLDER_LOCATION):
                        success("Scanned Folder Cleared!")
                    else:
                        warning("Scanned Folder NOT Cleared!")
                    break
                else:
                    if not ONE_FILE_MODE:
                        retry = raw_input(error("No Files Found in Current Folder! Retry? (y) "))
                        if ('n' or 'N') in retry:
                            break
                    else:
                        print "[INFO] Awaiting File Transfer..."
                        while True: # Check for a new File being Added to the Folder every X seconds
                            if (isFolderFilled(SCANNED_DOCUMENTS_FOLDER_LOCATION)):
                                debug("File Transfer Complete! Initizating Copy Protocol...")
                                break
                            time.sleep(0.5)
            if PLAY_SOUND:
                beep(SOUND_FILENAME)
            if ASK_TO_SYNC:
                psYnc = raw_input("[PROMPT] Confirm SyncToy Sync? (n) ")
                if ('y' or 'Y') in psYnc:
                    runSyncToy()
            if ASK_TO_CONTINUE:
                pCont = raw_input("Do you have more files? (y) ")
                if ('n' or 'N') in pCont:
                    break
            print "\n"
            
            
        

    





