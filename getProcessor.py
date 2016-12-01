import subprocess
import platform

def getProcessor():
    '''
    http://stackoverflow.com/questions/4842448/getting-processor-information-in-python
    http://stackoverflow.com/questions/18244126/python3-subprocess-output
    
    Returns "Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz Intel64 Family 6 Model 60 Stepping 3, GenuineIntel"
    instead of
    "Intel64 Family 6 Model 60 Stepping 3, GenuineIntel"
    '''
    if platform.system() == "Windows":
        family = platform.processor()
        name = subprocess.getoutput(["wmic","cpu","get","name"]).strip().split("\n")[2]
        return name
    elif platform.system() == "Darwin":
        return subprocess.check_output(['/usr/sbin/sysctl', "-n", "machdep.cpu.brand_string"]).strip()
    elif platform.system() == "Linux":
        command = "cat /proc/cpuinfo"
        return subprocess.check_output(command, shell=True).strip()
    return ""

