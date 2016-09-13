import re
import socket
import struct
import time

VERSION = "1.15"

class UTPlayer(object):
    """storage class with name cleanup"""
    def __init__(self):
        self.pid = 0
        self.sid = 0
        self.sidc = 0
        self.name = 0
        self.score = 0
        self.ping = 0
        self.team = 0

    def set_name(self, name):
        self.name = self.clean_name(name)

    def get_summary(self):
        self.find_team()
        return (self.name, self.pid, self.score, self.ping, self.sidc,
                self.team)

    def find_team(self): #included for compatibility
        return self.team

    def clean_name(self, s):
        return clean_name(s)

    def parse(self):
        self.find_team()
        self.name = self.clean_name(self.name)
        if self.score > 2**31:
            self.score = int(self.score-2**32)

class GSServer(object):
    def __init__(self, addr, port=7787, timeout=None):
        if type(timeout) == type(None): timeout = 0.4 #python pls
        self.timeout = timeout
        self.addr = addr
        self.port = port
        self.dest = (addr, port)
        self.udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpsock.setblocking(0)
        self.udpsock.settimeout(timeout)
        self.debug = False

    def query(self, init="info", pkl = 5):
        """init is the value of the last byte, pkl is max packets"""
        hdr = bytearray("\\%s\\" % init)
        self.udpsock.sendto(hdr, self.dest)
        recv_addr = ''
        out = ''
        p = None
        t = time.time()
        while time.time()-t < 2.5*self.timeout:
            try: p = self.udpsock.recvfrom(8192)
            except: p = ('', ('', ''))
            recv_addr = p[1][0]
            if recv_addr == self.addr:
                recv_addr = '' #necessary?
                out += p[0]
            if len(out) >= 7:
                if out[-7:] == '\\final\\': break
        return out

    def lp_str(self, s):
        l = ord(s[0])
        if s[l] == '\x00': return (s[1:l], s[l+1:])
        l = max(0, l-3)
        l = s.index('\x00', l)
        return (s[1:l], s[l+1:])

    def parse_query(self, query=None, qtype='info'):
        if type(query) != str:
            query = self.query(init=qtype)[1:-7]
        query = query.split('\\')
        i = 0
        out = dict()
        while True:
            if i > len(query)-2: break
            out[query[i]] = query[i+1]
            i += 2
        return out
        
    def parse_players(self, query=None):
        if type(query) != dict:
            query = self.query(init='players')[1:-7]
        query = self.parse_query(query)
        pl = []
        if len(query) == 0: return [] #maybe we should raise...?
        pc = 0
        if self.debug: print query
        while True:
            if ("player_%d" % pc) not in query.keys(): break
            p = UTPlayer()
            #set player id to player index
            p.pid = pc
            p.set_name(query["player_%d" % pc])
            if self.debug: print p.name
            p.ping = int(query["ping_%d" % pc].strip())
            p.score = int(query["frags_%d" % pc])
            p.sid = None #no equivalent
            p.team = int(query["team_%d" % pc])
            p.parse()
            pl.append(p)
            if self.debug: print p.get_summary()
            if self.debug:
                print "Record parsed: %s" % repr(pc)
                print "ID           : %s" % repr(pc)
                print "Name length  : %d" % len(query["player_%d" % pc])
                print "Name         : %s" % repr(query["player_%d" % pc])
                print "Ping         : %s" % repr(int(query["ping_%d" % pc]\
                                                     .strip()))
                print "Score        : %s" % repr(int(query["frags_%d" % pc]))
                print "StatsID      : %s" % repr(None)
            pc += 1
        return pl


def clean_name(s):
    o = re.sub("\x1b...", "", s)
    o = re.sub("[\x00-\x1f]", "", o)
    return o

def test(addr="74.91.115.188", exqtype=3):
    s = GSServer(addr)
    basic_query = s.parse_query()
    players_query = s.parse_query(qtype='players')
    print "Target: %s" % s.addr
    print "Basic Server Information:"
    for q in basic_query.keys():
        print "    %s: %s" % (q, basic_query[q])
    print "\nTeam Information:"
    for q in players_query.keys():
        print "    %s: %s" % (q, players_query[q])
