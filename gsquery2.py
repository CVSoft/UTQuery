import re
import socket
import struct
import time

VERSION = "2.0"

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
        self.server = (None, None)

    def __repr__(self):
        return "UTPlayer(%s)" % self.name

    def set_name(self, name):
        self.name = clean_name(name)

    def get_summary(self):
        self.find_team()
        return (self.name, self.pid, self.score, self.ping, self.sidc,
                self.team)

    def set_server(self, addr, do_correct=True):
        if type(addr) == str: addr = (addr, 7777)
        if do_correct:
            self.server = (addr[0], addr[1] - 10)
        else:
            self.server = addr

    def find_team(self): #included for compatibility
        return self.team

    def parse(self):
##        self.find_team() # literally does nothing on GS UTPlayers
        self.name = clean_name(self.name)
        if self.score > 2**31:
            self.score = int(self.score-2**32)

class GSMultiServer(object):
    def __init__(self, addr, timeout=None):
        """addr is an iterable of (host, port) pairs"""
        if type(timeout) == type(None): timeout = 0.4
        self.timeout = timeout
        if len(addr) == 0: raise IndexError # why this?
        if type(addr) == tuple:
            if len(addr) == 2:
                if type(addr[1]) == int: addr = (addr,)
        self.dstlist = list()
        for dst in addr:
            if len(dst) == 1 and type(dst) == tuple:
                dst = (dst[0], 7787)
            elif len(dst) == 1 and type(dst) == str:
                raise ValueError # check your list/tuple format
            elif type(dst) == str:
                dst = (dst, 7787)
            self.dstlist.append(dst)
        self.udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpsock.setblocking(0)
        self.udpsock.settimeout(timeout)
        self.debug = False

    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        self.udpsock.close()

    def send_query(self, init="info"):
        """init is the value of the last byte, pkl is max packets"""
        if len(self.dstlist) == 0: return dict()
        hdr = bytearray("\\%s\\" % init)
        out = dict()
        for dst in self.dstlist:
            self.udpsock.sendto(hdr, dst)
            out[dst] = ''
        recv_addr = ('', 0)
        p = None
        t = time.time()
        while time.time()-t < 2.5*self.timeout:
            try: p = self.udpsock.recvfrom(8192)
            except: p = None
            if not p:
                time.sleep(0.001) # power management
                continue
            recv_addr = p[1]
            try:
                out[recv_addr] += p[0]
            except KeyError:
                print "Not receiving from %s:%d" % recv_addr
            c = 0
            for k in out:
                if out[k].endswith("\\final\\"): c += 1
            if c == len(out): break
        return out

    def query(self, qtype='info', clean=True):
        qd = self.send_query(init=qtype)
        outd = dict()
        for k in qd:
            try:
                q = qd[k][1:-7].split('\\')
            except IndexError:
                outd[k] = dict()
                continue
            i = 0
            out = dict()
            while True:
                if i > len(q)-2: break
                if clean: out[q[i]] = clean_name(q[i+1])
                else: out[q[i]] = q[i+1]
                i += 2
            outd[k] = out
        return outd
        
    def players(self):
        qd = self.query(qtype="players")
        outd = dict()
        for k in qd:
            if not qd[k]:
                outd[k] = []
                continue
            pl = []
            pc = 0
            while True:
                if ("player_%d" % pc) not in qd[k].keys(): break
                p = UTPlayer()
                #set player id to player index
                p.pid = pc
                p.set_name(qd[k]["player_%d" % pc])
                if self.debug: print p.name
                p.ping = int(qd[k]["ping_%d" % pc].strip())
                p.score = int(qd[k]["frags_%d" % pc])
                p.sid = None #no equivalent
                p.team = int(qd[k]["team_%d" % pc])
                p.set_server(k)
                p.parse()
                pl.append(p)
                pc += 1
            outd[k] = pl
        return outd

class GSServer(object):
    def __init__(self, addr, timeout=None):
        if type(timeout) == type(None): timeout = 0.4 #python pls
        self.timeout = timeout
        if type(addr) == str:
            addr = (addr, 7787)
        self.addr, self.port = addr # why
        self.dst = addr
        self.udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpsock.setblocking(0)
        self.udpsock.settimeout(timeout)
        self.debug = False

    def send_query(self, init="info", pkl = 5):
        """init is the value of the last byte, pkl is max packets"""
        hdr = bytearray("\\%s\\" % init)
        self.udpsock.sendto(hdr, self.dst)
        out = ''
        p = None
        t = time.time()
        while time.time()-t < 2.5*self.timeout:
            try: p = self.udpsock.recvfrom(8192)
            except: p = None
            if not p:
                time.sleep(0.001) # power management
                continue
            recv_addr = p[1]
            if recv_addr == self.dst:
                out += p[0]
            if out.endswith('\\final\\'): break
        return out

    def query(self, qtype='info'):
        q = self.send_query(init=qtype)[1:-7].split('\\')
        i = 0
        out = dict()
        while True:
            if i > len(q)-2: break
            out[q[i]] = q[i+1]
            i += 2
        return out
        
    def players(self):
        query = self.query(qtype="players")
        pl = []
        if len(query) == 0: return [] #maybe we should raise...?
        pc = 0
        while True:
            if ("player_%d" % pc) not in query.keys(): break
            p = UTPlayer()
            #set player id to player index
            p.pid = pc
            p.set_name(query["player_%d" % pc])
            p.ping = int(query["ping_%d" % pc].strip())
            p.score = int(query["frags_%d" % pc])
            p.sid = None #no equivalent
            p.team = int(query["team_%d" % pc])
            p.set_server(self.dst)
            p.parse()
            pl.append(p)
            pc += 1
        return pl


def lp_str(s):
    l = ord(s[0])
    if s[l] == '\x00': return (s[1:l], s[l+1:])
    l = max(0, l-3)
    l = s.index('\x00', l)
    return (s[1:l], s[l+1:])

def clean_name(s):
    o = re.sub("\x1b...", "", s)
    o = re.sub("[\x00-\x1f]", "", o)
    return o

def test(addr="74.91.115.188", exqtype=3):
    s = GSServer(addr)
    basic_query = s.query()
    players_query = s.players()
    print "Target: %s" % s.addr
    print "Basic Server Information:"
    for q in basic_query.keys():
        print "    %s: %s" % (q, basic_query[q])
    print "\nTeam Information:"
    for q in players_query:
        print "    %s: %s" % (q.name, q.score)
