#!/usr/bin/python

import sys

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import OVSController
from mininet.cli import CLI
import time
import os

myBandwidth = 50    # bandwidth of link ink Mbps
myDelay = ['10ms', '10ms']    # latency of each bottleneck link
myQueueSize = 1000  # buffer size in packets
myLossPercentage = 0   # random loss on bottleneck links

#
#           h2      h4       h6
#           |       |        |
#           |       |        |
#           |       |        |
#   h1 ---- S1 ---- S2 ----- S3 ---- h8
#           |  10ms |  10ms  |
#           |       |        |
#           |       |        |
#           h3      h5       h7
#
#

class ParkingLotTopo( Topo ):
    "Three switches connected to hosts. n is number of hosts connected to switch 1 and 3"
    def build( self, n=3 ):
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')
        switch3 = self.addSwitch('s3')
        print "User set queue length as : " + str(myQueueSize) + "!!!!"     
        # Setting the bottleneck link parameters (htb -> Hierarchical token bucket rate limiting)
        self.addLink( switch1, switch2, 
            bw=myBandwidth, 
            delay=myDelay[0], 
            loss=myLossPercentage, 
            use_htb=True,
            max_queue_size=myQueueSize,
            )
        self.addLink( switch2, switch3, 
            bw=myBandwidth, 
            delay=myDelay[1], 
            loss=myLossPercentage, 
            use_htb=True,
            max_queue_size=myQueueSize, 
            )

        for h in range(3*n - 1):
            host = self.addHost('h%s' % (h + 1))
            if h < n:
                self.addLink(host, switch1) # one host to switch 1 (h1, h2, h3)
            elif h < 2*n - 1:
                self.addLink(host, switch2) # n hosts to switch 2 (h4, h5)
            else:
                self.addLink(host, switch3) # n hosts to switch 3 (h6, h7, h8)


def perfTest(tcp_type):
    "Create network and run simple performance test"
    topo = ParkingLotTopo(n=3)
    net = Mininet( topo=topo,
                   host=CPULimitedHost, link=TCLink, controller = OVSController)
    net.start()
    print("Dumping host connections")
    dumpNodeConnections( net.hosts )
    print("Testing network connectivity")
    net.pingAll()
    # CLI( net )  # start mininet interface

    # task start here
    print "User set tcp type as : " + tcp_type + "!!!!"  
    TCP_TYPE = tcp_type
    TIME = 100
    h1, h3, h8 = net.get('h1', 'h3', 'h8')

    h8.cmd('iperf3 -s -i 1 > h8_server_%s_%d.txt &' % (TCP_TYPE, myQueueSize))
    print("h8 start as a server")

    h1.cmd('iperf3 -c 10.0.0.8 -t %d -C %s > flow_%s_%d.txt &' % (TIME, TCP_TYPE, TCP_TYPE, myQueueSize))
    print("h1 start to send tcp request to h8")

    h3.cmd('ping 10.0.0.7 -i 1 -c %d > pingResult_%s_%d.txt &' % (TIME, TCP_TYPE, myQueueSize))
    print("h3 start to ping h7")

    print "waiting for background process " + str(TIME) + " sec"
    time.sleep(TIME)
    # task end here


    net.stop() # exit mininet

if __name__ == '__main__':
    tcp_type = sys.argv[1]
    myQueueSize = int(sys.argv[2])
    os.system("sudo mn -c") # clear all previous mininet config
    os.system("killall /usr/bin/ovs-testcontroller")
    setLogLevel( 'info' )
    print("\n\n\n ------Start Mininet ----- \n\n")
    perfTest(tcp_type)
    print("\n\n\n ------End Mininet ----- \n\n")

