import os
import string
import sys
import time
from traceback import format_tb

import UTQuery

class Server(object):
    def __init__(self, addr, port=7778, team_override = False, width=80):
        self.server = UTQuery.UTServer(addr, port)
        self.set_strings(width)
        self.hide_virtual = False
        self.name = None
        self.game_type = None
        self.map = None
        self.team_server = None
        #for 3SPN-hlm which doesn't poll properly
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
            self.name = si["Server Name"]
            self.game_type = si["Game Type"]
            self.map = si["Map Name"]
            self.team_server = (si["Game Type"] not in ["xDeathMatch"]) \
                               or self.team_override
        except:
            #don't update if failure
            self.name, self.game_type, self.map, self.team_server = b

    def get_all_players(self, force_update=True):
        if force_update: self.get_server_info()
        fstr = '{:<%d}  {:>3d} {:>4d} ms' % (self.tcw - 13)
        pl = self.server.parse_players()
        if len(pl) == 0:
            return tuple()
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
        pl = self.get_all_players()
        #no rts/bts, no teams, but we need to filter fakes
        fl = []
        for p in pl:
            if p[0].ping == 0 and (' ' in p[0].name or len(p[0].name) == 0):
                fl.append(pl.index(p))
        if self.hide_virtual:
            for i in sorted(list(set(fl)), reverse=True): pl.pop(i)
        #sort 0-score players into spec (BAD! but I don't care)
        pt, spec = ([], []) #pt = playing team
        for p in pl:
            if p[0].score == 0: spec.append(p)
            else: pt.append(p)
        #sort
        pt = sort_by_score(pt)
        spec = sort_by_ping(spec)
        #equalize lengths of lists
        while len(pt) != len(spec):
            if len(pt) > len(spec):
                spec.append((None, ' '*self.tcw))
            elif len(spec) > len(pt):
                pt.append((None, ' '*self.tcw))
        #title bar
        o = [self.thick_bar]
        if type(self.name) == str:
            o.append(self.ftext.format(self.name))
            if type(self.map) == str and type(self.game_type) == str:
                o.append(self.ftext.format("Playing %s on %s" % (self.game_type,
                                                                 self.map)))
            o.append(self.split_bar)
        o.append(self.stext.format("Players", "Spectators"))
        o.append(self.split_bar)
        #players
        for i in xrange(min(len(pt), len(spec))):
            o.append(self.stext.format(pt[i][1], spec[i][1]))
        #footer
        o.append(self.thin_bar)
        if nl:
            o = map(lambda q:q+'\n', o)
        if show:
            for l in o: print l
        return o

    def get_players_team(self, show=False, nl=False):
        pl = self.get_all_players()
        #find team score totals
        rts, bts = (None, None)
        fl = [] #indices of non-player spectators
        for p in pl:
            if p[0].ping == 0 and (' ' in p[0].name or len(p[0].name) == 0):
                if self.hide_virtual: fl.append(pl.index(p))
                if "red" in p[0].name.lower():
                    rts = p[0].score
                    if not self.hide_virtual: fl.append(pl.index(p)) #no dupes
                elif "blue" in p[0].name.lower():
                    bts = p[0].score
                    if not self.hide_virtual: fl.append(pl.index(p))
        for i in sorted(list(set(fl)), reverse=True): pl.pop(i)
        if type(rts) != type(None): rts = "Red Team - %d" % rts
        else: rts = "Red Team"
        if type(bts) != type(None): bts = "Blue Team - %d" % bts
        else: bts = "Blue Team"
        rt, bt, spec = ([], [], [])
        #sort player tuples into teams
        for p in pl: [spec, rt, bt][p[0].team].append(p)
        rt, bt = map(sort_by_score, [rt, bt])
        spec = sort_by_ping(spec)
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
        o.append(self.stext.format(rts, bts))
        o.append(self.split_bar)
        #team player list
        for i in xrange(min(len(rt), len(bt))):
            o.append(self.stext.format(rt[i][1], bt[i][1]))
##      o.append(fstr.format(' ', ' '))
        #spec separator
        if len(spec) > 0:
            o.append(self.thin_bar)
            #spec list
            o.append(self.ftext.format('Spectators'))
            for i in xrange(len(spec)):
                o.append(self.ftext.format(spec[i][1]))
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
                except: text = ["Connection failure"]
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
main()
