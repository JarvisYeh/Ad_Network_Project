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

myBandwidth = 100   # bandwidth of link ink Mbps
myDelay = '10ms'    # latency of the bottleneck link
myQueueSize = 1000  # buffer size in packets
myLossPercentage = 0   # random loss on bottleneck links

#
#   h1 ---- S1 ---- S2 ----- h2
#           |       |
#           h3      h4
#

class ParkingLotTopo( Topo ):
    "Three switches connected to hosts. n is number of hosts connected to switch 1 and 3"
    def build(self):
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')
        
        # Setting the bottleneck link parameters (htb -> Hierarchical token bucket rate limiting)
        self.addLink( switch1, switch2, 
            bw=myBandwidth, 
            delay=myDelay, 
            loss=myLossPercentage, 
            use_htb=True,
            max_queue_size=myQueueSize,
            )

        host = self.addHost('h1')
        self.addLink(host, switch1)
        host = self.addHost('h3')
        self.addLink(host, switch1)

        host = self.addHost('h2')
        self.addLink(host, switch2)
        host = self.addHost('h4')
        self.addLink(host, switch2)


def perfTest(tcp_type):
    "Create network and run simple performance test"
    topo = ParkingLotTopo()
    net = Mininet( topo=topo,
                   host=CPULimitedHost, link=TCLink, controller = OVSController)
    net.start()
    print("Dumping host connections")
    dumpNodeConnections( net.hosts )
    print("Testing network connectivity")
    net.pingAll()
    # CLI( net )

    TCP_TYPE_first = "cubic"
    TCP_TYPE_second = "bbr"

    run_time_tot = 500 # total iperf3 runtime, in seconds. I recommend more than 300 sec.

    h1, h2, h3, h4, h5, h6, h7, h8 = net.get('h1','h2','h3','h4','h5','h6','h7','h8')
    

    # h3 ping h4
    h3.cmd('ping 10.0.0.4 -i 1 -c %d > h3_ping_result_%s &' % (run_time_tot, str(myQueueSize)))

    # Receiver h2
    h2.cmd('iperf3 -s -i 1 > h1_server_%s &' % (str(myQueueSize)))
    
    # First, start to send the flow 1 : h1 --> h2, cubic
    print("--- h1 sends to h2 with 1 TCP (%s) flow during %d sec ---" % (TCP_TYPE_first, run_time_tot))
    h1.cmd('iperf3 -c 10.0.0.2 -t %d -C %s > flow1_%s_%s &' % (run_time_tot, TCP_TYPE_first, TCP_TYPE_first, str(myQueueSize)))

    # wait 10 seconds 
    # time.sleep(10)

    # Secondly, start to send the flow 2 : h8 --> h4
    print("--- h1 sends to h2 with 1 TCP (%s) flow during %d sec ---" % (TCP_TYPE_second, run_time_tot))
    h1.cmd('iperf3 -c 10.0.0.2 -t %d -C %s > flow2_%s_%s &' % (run_time_tot, TCP_TYPE_second, TCP_TYPE_second, str(myQueueSize)))

    # wait enough until all processes are done.
    print("wait for process time: ", run_time_tot)

    time.sleep(run_time_tot + 10)
    # CLI(net)
    net.stop() # exit mininet



if __name__ == '__main__':

    myQueueSize = int(sys.argv[1])
    
    print "User set queue size to: " + str(myQueueSize)

    os.system("sudo mn -c")
    os.system("killall /usr/bin/ovs-testcontroller")
    setLogLevel( 'info' )
    print("\n\n\n ------Start Mininet ----- \n\n")
    perfTest(tcp_type)
    print("\n\n\n ------End Mininet ----- \n\n")

