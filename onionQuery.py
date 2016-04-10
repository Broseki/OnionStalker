from onion_py.manager import Manager
from onion_py.caching import OnionSimpleCache

manager = Manager(OnionSimpleCache())


def getnickname(fingerprint):
    details = manager.query('summary')
    x = 0
    while True:
        if details.relays[x].fingerprint == fingerprint:
            return details.relays[x].nickname
        else:
            x += 1

def running(fingerprint):
    details = manager.query('summary')
    x = 0
    try:
        while True:
            if details.relays[x].fingerprint == fingerprint:
                return details.relays[x].running
            else:
                x += 1
    except:
        return "na"

def getbandwidth(fingerprint):
    details = manager.query('details')
    x = 0
    while True:
        if details.relays[x].fingerprint == fingerprint:
            return details.relays[x].bandwidth
        else:
            x += 1