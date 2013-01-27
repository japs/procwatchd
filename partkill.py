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

__version__ = "0.4"

from multiprocessing import cpu_count
from subprocess import check_output
from os import kill, popen
from re import search
from logging import basicConfig, debug, info, warning, error ,critical, \
                    DEBUG, INFO, WARNING, ERROR, CRITICAL
from email.mime.text import MIMEText
from smtplib import SMTP

#USER DEFINITE STUFF
LOG_FILE = 'procwatch.log'
LOG_VERBOSITY = INFO
DRY_RUN = True           # If True, it doesn't actually kill anybody
UPDATE_TIME = 2 #seconds

SMTP_SERVER = "smtp.example.eu:25"
ADMIN_EMAIL = "admin@admin"
EMAIL_DOMAIN = "@domain.eu"
EMAIL_SUBJECT = "Process Killed for improper use of host"


# processes that will be killed only in the event of a memory quick_action
PROC_WHITELIST = ['cp', 'ssh', 'scp', 'tar', 'iceweasel']

#LIMITS          # unit
MEM_QUICK_ACTION = 80 # %
MEM_KILL   = 15  # %
MEM_WATCH  = 8   # %
CPU_KILL   = 95  # %
CPU_WATCH  = 60  # %
TIME_KILL  = 600 # seconds
TIME_WATCH = 450 # seconds

#Col number for ps aux
PS_COL_USR  = 0
PS_COL_PID  = 1
PS_COL_CPU  = 2 
PS_COL_MEM  = 3
PS_COL_TIME = 9
PS_COL_CMD  = 10 # and following

#logger setup
basicConfig(filename=LOG_FILE, level=LOG_VERBOSITY,
            format='%(asctime)s - %(levelname)s: %(message)s')


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
            annihilate(self, 9)
        elif float(self.mem) > MEM_WATCH:
            pass

    def check_cpu(self, CPU_KILL, CPU_WATCH):
        if float(self.cpu) > CPU_KILL:
            annihilate(self, 9)
        elif float(self.cpu) > CPU_WATCH:
            pass

    def check_time(self, TIME_KILL, TIME_WATCH):  
        if timesec(self.time) > TIME_KILL:     
            annihilate(self, 9)
        elif timesec(self.time) > TIME_WATCH:
            pass

    def check_time_cpu(self, TIME_WATCH, TIME_KILL,
                       CPU_WATCH, CPU_KILL):
        if(timesec(self.time) > TIME_KILL and float(self.cpu) > CPU_WATCH):
            annihilate(self, 9)
        if(timesec(self.time) > TIME_WATCH and float(self.cpu) > CPU_WATCH):
            pass

    def all_checks(self, MEM_KILL, MEM_WATCH,
                   CPU_KILL, CPU_WATCH,
                   TIME_KILL, TIME_WATCH):
        status = 0x11FEBEEF
        status = self.check_memory(MEM_KILL, MEM_WATCH)
        if not status == 0xDEADBEEF:
            status = self.check_cpu(CPU_KILL, CPU_WATCH)
        if not status == 0xDEADBEEF:
            status = self.check_time(TIME_KILL, TIME_WATCH)
        if not status == 0xDEADBEEF:
            self.check_time_cpu(TIME_WATCH, TIME_KILL, 
                                CPU_WATCH, CPU_KILL)
    def __repr__(self):
        r = "Process PID %s (%s)\n" %(self.pid, self.usr)
        r += "                              "
        r += "MEM %s\tCPU %s\tTIME %s\n" %(self.mem, self.cpu, 
                                                  self.time)
        r += "                              "
        r += self.cmd
        return r

class Processes(dict):
    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)

    def patrol(self):
        for p in self:
            self[p].all_checks(MEM_KILL, MEM_WATCH, 
                               CPU_KILL, CPU_WATCH, 
                               TIME_KILL, TIME_WATCH)


def annihilate(proc, signal):
    if not DRY_RUN:
        kill(int(proc.pid), signal)
    best_wishes(proc)
    critical("Killed process " + str(proc))
    return 0xDEADBEEF

def send_mail(from_address, to_address, msg):
    connection = SMTP(SMTP_SERVER)
    #double check the behaviour of set_debuglevel and eventually
    #integrate it in the logging facility
    connection.set_debuglevel(False)
    connection.sendmail(from_address, to_address, msg.as_string())
    connection.quit()


def best_wishes(proc):
    ''' Send a mail with best wishes to the owner of process pid.
    '''
    if not DRY_RUN:
        mailtext="Dear "+proc.usr+",\nyour process "+proc.cmd+" was killed " \
                  +"because it was using too much resources:\n" \
                  +proc.cpu+"% of CPU\n" \
                  +proc.mem+"% of RAM\n" \
                  +"for "+proc.time+" seconds\n"

        msg = MIMEText (mailtext)
        msg["From"] = ADMIN_EMAIL
        msg["To"] = proc.usr + EMAIL_DOMAIN
        msg["Subject"] = EMAIL_SUBJECT
        
        send_mail(ADMIN_EMAIL, 
                  [proc.usr + EMAIL_DOMAIN, ADMIN_EMAIL],
                  msg)
        if status != 0:
            error( "Sendmail exit status: %d" %status)
        else:
            info("Mail sent to %s for process %s" %(proc.usr, proc.pid))
    else:
        info("DRYRUN, would send mail to %s for process %s" %(proc.usr,
                                                              proc.pid))


def get_ps_output(root=False, quick_action=MEM_QUICK_ACTION):
    ''' Fetch the output of `ps aux` and return it as a list,
        one per output line.
        Optionally omit the processes of user root by setting
        root=False (default behaviour).
        quick_action allows the program to immediately take action
        against a process if it takes more %MEM than the value of this 
        variable.
    '''
    
    raw = check_output(['ps', 'aux'])
    raw = raw.decode()
    out = raw.split('\n')
    processes = Processes()
    for o in out[1:len(out)-1]:   # last line of out is empty
        osplit = o.split()
        if ( not root and osplit[PS_COL_USR]=='root'):
            continue
        else:
            # create process object append to list
            p = Process( osplit[PS_COL_USR],
                         osplit[PS_COL_PID],
                         osplit[PS_COL_CPU],
                         osplit[PS_COL_MEM],
                         osplit[PS_COL_TIME],
                         osplit[PS_COL_CMD]  )
        if (quick_action > 0 and float(p.mem) > quick_action):
                annihilate(p, 9)
        else:
            whitelist = False
            for proc in PROC_WHITELIST:
                cmdsplit = (p.cmd).split()[0]
                whitelisted = search('/' + proc + '$', cmdsplit)
                if whitelisted != None:
                    whitelist = True
            if not whitelist:
                # append to list
                processes[p.pid] = p
            else:
                debug("WHITELISTED " + str(p))
    return processes


if __name__ == '__main__' :
    from time import sleep
    from sys import exit
    try:
        info("Patrolling started")
        while True:
            debug("patrol update")
            processes = get_ps_output(root=False, quick_action=60)
            processes.patrol()
            sleep(UPDATE_TIME)
    except KeyboardInterrupt:
        info("Patrolling stopped via keyboard interrupt")
        exit(0)
    
