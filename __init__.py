import platform
import subprocess

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
        return subprocess.getoutput(command).split(": ")[1].strip

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
        return subprocess.getoutput(command).split(":         ")[1].strip() #this is bad and could probably be handled better...

print("SimpleMon")

print("Getting Host Details")

hostDetails = {}
hostDetails["os"] = platform.system() + " " + platform.release() # "Windows" + " " + "7"
hostDetails["arch"] = platform.architecture()[0] # we only want 64bits or 32bits
hostDetails["processor"] = getProcessor()
hostDetails["ram"] = getRam()
print(hostDetails)

