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

    def find_team(self):
        m = self.sid & 0x60000000
        self.team = 0
        if m > 1:
            self.team = 1
            if m > 0x30000000: self.team = 2
        return self.team

    def clean_name(self, s):
        return clean_name(s)

    def parse(self):
        self.find_team()
        self.name = self.clean_name(self.name)
        self.sidc = int(self.sid & 0x9fffffff)
        if self.score > 2**31:
            self.score = int(self.score-2**32)

class UTServer(object):
    def __init__(self, addr, port=7778, timeout=None):
        if type(timeout) == type(None): timeout = 0.4 #python pls
        self.timeout = timeout
        self.addr = addr
        self.port = port
        self.dest = (addr, port)
        self.udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpsock.setblocking(0)
        self.udpsock.settimeout(timeout)
        self.debug = False

    def query(self, init=0, pkl = 5):
        """init is the value of the last byte, pkl is max packets"""
        hdr = bytearray([0x80, 0, 0, 0, init])
        self.udpsock.sendto(hdr, self.dest)
        t = time.time()
        recv_addr = ''
        out = ''
        p = None
        pkc = 0
        while time.time()-t < 1.5*self.timeout and pkc < pkl:
            try: p = self.udpsock.recvfrom(8192)
            except: p = ('', ('', ''))
            recv_addr = p[1][0]
            if recv_addr == self.addr:
                recv_addr = ''
                pkc += 1
                ##print "Packet %d of %d" % (pkc, pkl)
                if pkc > 1:
                    p = list(p)
                    p[0] = p[0][5:]
                    p = tuple(p)
                out += p[0]
        return out

    def parse_exquery(self, query=None, qtype=1, qpkl=5):
        if type(query) != str:
            query = self.query(qtype, pkl=qpkl)
        ql = map(lambda q:q[1:], query[5:].split('\x00'))
        dd = dict() #duplicate key counts
        qd = dict()
        mut_count = 0
        for i in xrange(0, len(ql)-1, 2):
            if ql[i].lower() in map(lambda q:q.lower(), qd.keys()):
                k = ql[i].lower()
                if k not in dd.keys():
                    dd[k] = 0
                dd[k] += 1
                ql[i] += str(dd[k])
            qd[ql[i]] = ql[i+1]
        return qd

    def get_tickrate(self, query=None):
        q = self.parse_exquery(query)["Server Tickrate"]
        return (float(q.split(' ')[0][4:]), float(q.split(' ')[1][4:]))

    def lp_str(self, s):
        l = ord(s[0])
        if s[l] == '\x00': return (s[1:l], s[l+1:])
        l = max(0, l-3)
        l = s.index('\x00', l)
        return (s[1:l], s[l+1:])

    def parse_query(self, query=None):
        if type(query) != str:
            query = self.query(0)
        #lop off unused elements (BAD?)
        query = query[10:]
        a = list(struct.unpack('=II', query[:8]))
        q = query[8:]
        for i in xrange(3):
            p, q = self.lp_str(q) #server name, map name, game mode
            a.append(clean_name(p))
        a += list(struct.unpack('=4I', q[:16])) #cur, max players, ping, flags
        p, q = self.lp_str(q[16:])
        a.append(p)
        return {"Server Port":a[0],
                "Query Port":a[1],
                "Server Name":a[2],
                "Map Name":a[3],
                "Game Type":a[4],
                "Current Players":a[5],
                "Maximum Players":a[6],
                "Ping":a[7],
                "Flags":a[8],
                "Skill":a[9]}

    def parse_players(self, query=None, rem_fakes=True):
        if type(query) != str:
            query = self.query(2)
        #oh god
        i = 5 #skip the header [edit: uhh]
        pl = []
        if len(query) == 0: return [] #no players online == no data recv'd?
        while True:
            p = UTPlayer()
            p.pid = struct.unpack("=I", query[i:i+4])[0]
            i += 4
            n = ord(query[i])
            #[in]sanity checking
            if query[i+n] != '\x00':
                n -= 3
                while query[i+n] != '\x00':
                    if query[i+n] == '\x1b': #colored char width
                        n += 4
                        continue
                    n += 1 #stop at first null terminator
            p.set_name(query[i+1:i+n])
            if self.debug: print p.name
            i += n+1
            p.ping, p.score, p.sid = struct.unpack("=III",
                                                   query[i:i+12])
            i += 12
            p.parse()
            pl.append(p)
            if self.debug: print p.get_summary()
            if i > len(query)-14: break
            if self.debug:
                print "Record parsed: %s" % repr(query[i-n-17:i])
                print "ID           : %s" % repr(query[i-n-17:i-n-13])
                print "Name length  : %d" % ord(query[i-n-13])
                print "Name         : %s" % repr(query[i-n-12:i-12])
                print "Ping         : %s" % repr(query[i-12:i-8])
                print "Score        : %s" % repr(query[i-8:i-4])
                print "StatsID      : %s" % repr(query[i-4:i])
        i = 0
        while i < len(pl) and rem_fakes:
            if "team" in pl[i].name.lower() and pl[i].ping == 0:
                pl.pop(i)
            else: i += 1
        return pl


def clean_name(s):
    o = re.sub("\x1b...", "", s)
    o = re.sub("[\x00-\x1f]", "", o)
    return o

def test(addr="74.91.115.188", exqtype=3):
    s = UTServer(addr)
    basic_query = s.parse_query()
    extended_query = s.parse_exquery(None, exqtype)
    print "Target: %s" % s.addr
    print "Basic Server Information:"
    for q in basic_query.keys():
        print "    %s: %s" % (q, basic_query[q])
    print "\nExtended Server Information:"
    for q in extended_query.keys():
        print "    %s: %s" % (q, extended_query[q])
