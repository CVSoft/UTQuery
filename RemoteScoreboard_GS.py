import os
import string
import sys
import time
from traceback import format_tb

import GSQuery

## proof of how easy it is to modify GSQuery to replace UTQuery

class Server(object):
    def __init__(self, addr, port=7787, team_override = False, width=80,
                 timeout=None):
        self.server = GSQuery.GSServer(addr, port, timeout=timeout)
        self.set_strings(width)
        self.hide_virtual = False
        self.name = None
        self.game_type = None
        self.map = None
        self.team_server = None
        #for 3SPN-hl which doesn't poll properly (GameSpy query polls correctly)
        self.team_override = team_override

    def set_strings(self, width=80):
        self.width = width
        self.tcw = width/2 - 3 #two column width
        self.stext = "| {:^%d} | {:^%d}|" % (self.tcw, self.tcw)
        self.ftext = "| {:^%d} |" % (self.width - 4)
        self.thick_bar = '+' + '='*(self.width - 2) + '+'
        self.thin_bar = self.thick_bar.replace('=', '-')
        self.split_bar = '+' + '-'*(self.tcw + 2) + '+' + \
                         '-'*(self.tcw + (2 - self.tcw % 2)) + '+'
        
    def get_server_info(self):
        b = (self.name, self.game_type, self.map, self.team_server)
        try:
            si = self.server.parse_query() #basic query
            self.name = si["hostname"]
            self.game_type = si["gametype"]
            self.map = si["mapname"]
            self.team_server = (si["gametype"] not in ["xDeathMatch"]) \
                               or self.team_override
        except:
            #don't update if failure
            self.name, self.game_type, self.map, self.team_server = b

    def get_all_players(self, force_update=True):
        if force_update: self.get_server_info()
        fstr = '{:<%d}  {:>3d} {:>4d} ms' % (self.tcw - 13)
        pl = self.server.parse_players()
        if len(pl) == 0:
            return tuple() #if no players, server returns no data (UTQuery only)
        o = []
        for p in pl: o.append((p, fstr.format(p.name, p.score, p.ping)))
        return o

    def get_players(self, show=False, nl=False, team=None):
        if type(team) == bool: pass #why
        elif type(self.team_server) == type(None):
            try:
                self.get_server_info()
                team = self.team_server
            except:
                team = False
        else: team = self.team_server
        if team: return self.get_players_team(show, nl)
        return self.get_players_dm(show, nl)

    def get_players_dm(self, show=False, nl=False):
        pt = self.get_all_players()
        #sort
        pt = sort_by_score(pt)
        #title bar
        o = [self.thick_bar]
        if type(self.name) == str:
            o.append(self.ftext.format(self.name))
            if type(self.map) == str and type(self.game_type) == str:
                o.append(self.ftext.format("Playing %s on %s" % (self.game_type,
                                                                 self.map)))
            o.append(self.split_bar)
        o.append(self.ftext.format("Players"))
        if len(pl) > 0: o.append(self.split_bar)
        #players
        for p in pt:
            o.append(self.ftext.format(p[1]))
        #footer
        o.append(self.thin_bar)
        if nl:
            o = map(lambda q:q+'\n', o)
        if show:
            for l in o: print l
        return o

    def get_players_team(self, show=False, nl=False):
        pl = self.get_all_players()
        rt, bt= ([], [])
        #sort player tuples into teams
        for p in pl: [rt, bt][p[0].team].append(p)
        rt, bt = map(sort_by_score, [rt, bt])
        #there is certainly a better way for the following
        while len(rt) != len(bt):
            if len(rt) > len(bt):
                bt.append((None, ' '*self.tcw))
            elif len(bt) > len(rt):
                rt.append((None, ' '*self.tcw))
        #title bar
        o = [self.thick_bar]
        if type(self.name) == str:
            o.append(self.ftext.format(self.name))
            if type(self.map) == str and type(self.game_type) == str:
                o.append(self.ftext.format("Playing %s on %s" % (self.game_type,
                                                                 self.map)))
            o.append(self.split_bar)
        o.append(self.stext.format("Red Team", "Blue Team"))
        if len(pl) > 0: o.append(self.split_bar)
        #team player list
        for i in xrange(min(len(rt), len(bt))):
            o.append(self.stext.format(rt[i][1], bt[i][1]))
##      o.append(fstr.format(' ', ' '))
        #footer
        o.append(self.thin_bar)
        if nl:
            o = map(lambda q:q+'\n', o)
        if show:
            for l in o: print l
        return o


def sort_by_score(t):
    """sorts Player,str tuples by score"""
    sl = [x[0].score for x in t]
    return [x for (y,x) in sorted(zip(sl,t), key=lambda q:q[0])][::-1]

def sort_by_ping(t):
    """sorts Player,str tuples by ping"""
    pl = [x[0].ping for x in t]
    return [x for (y,x) in sorted(zip(pl,t), key=lambda q:q[0])]

def is_idle():
    return 'idlelib.__main__' in sys.modules

def clear():
    if is_idle():
        print '\n'*80 #a lot
        return
    if os.name == "nt": os.system("cls")
    else: sys.stderr.write("\x1b[2J\x1b[H")

def wait(t):
    tc = time.time()
    while time.time() - tc < t: time.sleep(0.05)

def main():
    try:
        if os.name == "nt" and not is_idle():
            os.system("mode con: cols=80 lines=25")
            os.system("chcp 1252")
            os.system("cls")
        #s = Server("66.150.121.88")
        if len(sys.argv) < 2: s = Server("74.91.115.188")
        elif len(sys.argv) == 2:
            s = Server(sys.argv[1])
        elif len(sys.argv) == 3:
            s = Server(sys.argv[1], int(sys.argv[2]))
        elif len(sys.argv) == 4:
            s = Server(sys.argv[1], int(sys.argv[2]))
            s.team_override = True
        else:
            raise ValueError("Check command-line syntax!")
        while True:
            try: text = s.get_players()
            except:
                try: text = s.get_players() #try again
                except:
                    text = ["Connection failure"] + \
                           map(lambda q:repr(q)+'\n',list(sys.exc_info()))
                    for l in format_tb(sys.exc_info()[-1]): print l
            clear()
            for l in text: sys.stdout.write(l)
            wait(10)
    except KeyboardInterrupt: pass
    except:
        print "Something went wrong! Error details:"
        for x in sys.exc_info()[:-1]:
            print x
        print "\nTraceback:"
        for x in format_tb(sys.exc_info()[-1]): print x
        raw_input()


if __name__ == "__main__":
    main()
