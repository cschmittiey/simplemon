import platform     #Platform data, such as OS type, release, etc
import subprocess   #Used for running local console commands
import sys          #Used to determine system python version, as we need Python 3 and not 2
import logging      #Well, it's used for logging. Importing it as l because I'm lazy and don't want to type logging everytime.
#Make sure we've got Python 3 here, or else weird errors will happen
'''
http://stackoverflow.com/questions/446052/how-can-i-check-for-python-version-in-a-program-that-uses-new-language-features
'''

req_version = (3,0)
cur_version = sys.version_info

if cur_version >= req_version:
    pass
else:
    print("Your Python interpreter is too old. Simplemon requires at least Python 3.")
    sys.exit(1) #Generally used to signify an error has occurred on Unix/POSIX systems. 

def getProcessor():
    '''
    http://stackoverflow.com/questions/4842448/getting-processor-information-in-python
    http://stackoverflow.com/questions/18244126/python3-subprocess-output
    
    Returns "Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz Intel64 Family 6 Model 60 Stepping 3, GenuineIntel"
    instead of
    "Intel64 Family 6 Model 60 Stepping 3, GenuineIntel"
    
    https://docs.python.org/2/library/string.html
    '''
    if platform.system() == "Windows":
        name = subprocess.getoutput(["wmic","cpu","get","name"]).split("\n")[2].strip()
        return name
    elif platform.system() == "Darwin":
        return subprocess.getoutput(['/usr/sbin/sysctl', "-n", "machdep.cpu.brand_string"]).strip()
    elif platform.system() == "Linux": 
        command = "cat /proc/cpuinfo | grep model\\ name"
        return subprocess.getoutput(command).split(": ")[1].split("\n")[0].strip() #This looks pretty ugly, but it prevents "\nmodel name" appended to the result. Not terribly sure why it's doing that, but under Fedora 26 it does. Don't think it did on my server (TODO) Check output across linuxes

def getRam():
    '''
    http://superuser.com/questions/197059/mac-os-x-sysctl-get-total-and-free-memory-size <--mac
    http://stackoverflow.com/questions/30228366/how-to-find-only-the-total-ram-in-python <--linux
    https://docs.python.org/2/library/string.html
    https://blogs.technet.microsoft.com/askperf/2012/02/17/useful-wmic-queries/ <-- windows
    
    TODO: consistent memory output? linux outputs it in kB, windows and mac in bytes.
    '''
    if platform.system() == "Windows":
        return subprocess.getoutput(["wmic","memorychip","get","capacity"]).split("\n")[2].strip()
    elif platform.system() == "Darwin":
        return subprocess.getoutput(['/usr/sbin/sysctl', "-n", "hw.memsize"]).strip() #hw.usermem and others report wrong values supposedly, but hw.memsize works.
    elif platform.system() == "Linux":
        command = "cat /proc/meminfo | grep MemTotal"
        return subprocess.getoutput(command).split(":        ")[1].strip() #this is bad and could probably be handled better...
'''
https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
'''

# create logger
l = logging.getLogger(__name__)
l.setLevel(logging.DEBUG)

# create console handler and set level to info -- we don't want console spam.
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create file handler and set level to debug
fh = logging.FileHandler('simplemon.log')
fh.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
l.addHandler(ch)

l.info("SimpleMon")
l.info("Getting Host Details")

hostDetails = {}
hostDetails["os"] = platform.system() + " " + platform.release() # "Windows" + " " + "7"
hostDetails["arch"] = platform.architecture()[0] # we only want 64bits or 32bits
hostDetails["processor"] = getProcessor()
hostDetails["ram"] = getRam()
print(hostDetails)
l.debug(hostDetails)

