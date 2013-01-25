#!/usr/bin/python

from multiprocessing import cpu_count
from subprocess import check_output
from os import kill

PS_COL_USR  = 0
PS_COL_PID  = 1
PS_COL_CPU  = 2 
PS_COL_MEM  = 3
PS_COL_TIME = 9
PS_COL_CMD  = 10 # and following

class User():
    def __init__(self, username):
        self.username = username
        self.memory = 0
        self.cpu = 0
        self.proclist = []

class Process():
    def __init__(self, usr, pid, cpu, mem, time, cmd):
        self.usr = usr
        self.pid = pid
        self.cpu = cpu
        self.mem = mem
        self.time = time
        self.cmd = cmd

def annihilate(pid, signal):
    kill(pid, signal)

def get_ps_output(root=True, quick_action=-1):
    ''' Fetch the output of `ps aux` and return it as a list,
        one per output line.
        Optionally omit the processes of user root by setting
        root=false.
        quick_action allows the program to immediately take action
        against a process if it takes more %MEM than the value of this 
        variable.
    '''
    raw = check_output(['ps', 'aux'])
    out = raw.split('\n')
    proclist = []
    for o in out:
        osplit = o.split()
        if (root and osplit[PS_COL_USR]=='root'):
            continue
        else:
            if (quick_action > 0 and osplit[PS_COL_MEM] > quick_action):
                annihilate(osplit[PS_COL_PID], 9)

            proclist.append( osplit[PS_COL_USR],
                             osplit[PS_COL_PID],
                             osplit[PS_COL_CPU],
                             osplit[PS_COL_MEM],
                             osplit[PS_COL_TIME],
                             osplit[PS_COL_CMD]  )
    return proclist




if __name__ == '__main__' :
    
