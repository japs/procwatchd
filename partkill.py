#!/usr/bin/python
# Copyright 2013 Jacopo Nespolo <jnespolo@gmail.com>
# Copyright 2013 Claudio Bonati <claudio.bonati82@gmail.com>
#
# This program is released under the terms of the GNU General Public License,
# either version 3 or, at your option, any following version as published by
# the Free Software Foundation.
# If you don't know the content of the license, realise that you're on the 21st
# century and look it up online!
#

__version__ = "0.1a"

from multiprocessing import cpu_count
from subprocess import check_output
from os import kill

#LIMITS          # unit
MEM_KILL   = 15  # %
MEM_WATCH  = 8   # %
CPU_KILL   = 95  # %
CPU_WATCH  = 60  # %
TIME_KILL  = 600 # seconds
TIME_WATCH = 450 # seconds


PS_COL_USR  = 0
PS_COL_PID  = 1
PS_COL_CPU  = 2 
PS_COL_MEM  = 3
PS_COL_TIME = 9
PS_COL_CMD  = 10 # and following

def timesec(t):
    tsplit=t.split(":")
    return 60*int(tsplit[0])+int(tsplit[1])
  

class User():
    def __init__(self, username):
        self.username = username
        self.memory = 0
        self.cpu = 0
        self.proclist = []

class Users(dict):
    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)

    def update_active_users(self, active_username_list):
        ''' Update the dictionary {username: User_obj}
            of the active users.
        '''
        #remove users that were active before and still are
        for usr in self.keys():
            if usr in active_username_list:
                active_username_list.remove(usr)
            else:
                del self[usr]
        #add newly found users
        for usr in active_username_list:
            self[usr] = User(usra)

    def update_user(userobj):
        self[userobj.username] = userobj

class Process():
    def __init__(self, usr, pid, cpu, mem, time, cmd):
        self.usr = usr
        self.pid = pid
        self.cpu = cpu
        self.mem = mem
        self.time = time
        self.cmd = cmd

    def check_memory(self, MEM_KILL, MEM_WATCH):
        if float(self.mem) > MEM_KILL:
            annihilate(int(self.pid), 9)
        elif float(self.mem) > MEM_WATCH:
            pass

    def check_cpu(self, CPU_KILL, CPU_WATCH):
        if float(self.cpu) > CPU_KILL:
            annihilate(int(self.pid), 9)
        elif float(self.cpu) > CPU_WATCH:
            pass

    def check_time(self, TIME_KILL, TIME_WATCH):  
        if timesec(self.time) > TIME_KILL:     
            annihilate(int(self.pid), 9)
        elif timesec(self.time) > TIME_WATCH:
            pass

    def check_time_cpu(self, TIME_WATCH, TIME_KILL,
                       CPU_WATCH, CPU_KILL):
        if(timesec(self.time) > TIME_KILL and float(self.cpu) > CPU_WATCH):
            annihilate(int(self.pid), 9)
        if(timesec(self.time) > TIME_WATCH and float(self.cpu) > CPU_WATCH):
            pass

    def all_checks(self, MEM_KILL, MEM_WATCH,
                   CPU_KILL, CPU_WATCH,
                   TIME_KILL, TIME_WATCH):
        status = 0x11FEBEEF
        status = self.check_memory(MEM_KILL, MEM_WATCH)
        if not status == 0xDEADBEEF:
            status = self.check_cpu(CPU_KILL, CPU_WATCH)
        if not status == 0x11FEBEEF:
            status = self.check_time(TIME_KILL, TIME_WATCH)
        if not status == 0x11FEBEEF:
            self.check_time_cpu(TIME_WATCH, TIME_KILL, 
                                CPU_WATCH, CPU_KILL)

class Processes(dict):
    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)

    def patrol(self):
        for p in self:
            self[p].all_checks(MEM_KILL, MEM_WATCH, 
                               CPU_KILL, CPU_WATCH, 
                               TIME_KILL, TIME_WATCH)
    
class Watchlist():
    def __init__(self):
        self.mem = {}
        self.cpu = {}
        self.users = {}

def annihilate(pid, signal):
    kill(pid, signal)
    best_wishes(pid)
    return 0xDEADBEEF

def best_wishes(pid):
    ''' Send a mail with best wishes to the owner of process pid.
    '''
    #TODO
    pass

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
    processes = Processes()
    for o in out[1:len(out)-1]:   # last line of out is empty
        osplit = o.split()
        if (root and osplit[PS_COL_USR]=='root'):
            continue
        else:
            if (quick_action > 0 and \
                float(osplit[PS_COL_MEM]) > quick_action):
                annihilate(int(osplit[PS_COL_PID]), 9)
            else:
                # create process object and append to list
                p = Process( osplit[PS_COL_USR],
                             osplit[PS_COL_PID],
                             osplit[PS_COL_CPU],
                             osplit[PS_COL_MEM],
                             osplit[PS_COL_TIME],
                             osplit[PS_COL_CMD]  )
                processes[p.pid] = p
    return processes


if __name__ == '__main__' :
  while True:
        processes = get_ps_output(root=False, quick_action=60)
        processes.patrol()

