def checksum(msg):
    q = 0
    for w in range(0, len(msg), 2):
        e = msg[w] + (msg[w+1] << 8)
        r = q+e
        q = (r & 0xffff) + (r >> 16)
    return ~q & 0xffff


def echo(ident, seqnum):
    """
    Y'know this should really all be in the standard library
    Thanks StackOverflow
    """

    import struct
    # packet type, code, checksum, identifier, sequence num
    info = struct.pack('BBHHH', 8, 0, 0, ident, seqnum)
    csum = checksum(info)
    return struct.pack('BBHHH', 8, 0, csum, ident, seqnum)


def trace(uri):
    """Trace a route"""
    import socket
    import time
    uri = (uri, 7)
    icmp = socket.getprotobyname('icmp')
    in_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    out_s = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    in_s.bind(('0.0.0.0', 0))
    in_s.settimeout(5)

    magic = 1
    last = '0.0.0.0'
    while True:
        rtt = 0
        attempts = 3
        for _ in range(attempts):
            out_s.setsockopt(socket.SOL_IP, socket.IP_TTL, magic)
            start = time.time_ns()
            out_s.sendto(echo(magic, magic), uri)
            this = in_s.recvfrom(1024)[1][0]
            end = time.time_ns()

            rtt += (end-start)/(1_000_000*attempts)

        if this != last:
            print(f'{magic}\t{this}\t{round(rtt,2)}ms')
            last = this
            magic += 1
        else:
            break


if __name__ == '__main__':
    import sys
    trace(sys.argv[1])
