route add default gw 192.168.7.1
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
https://machinekoder.com/machinekit-debian-stretch-beaglebone-black/


echo 'if [ -f ~/git/machinekit/scripts/rip-environment ]; then
    source ~/git/machinekit/scripts/rip-environment
    echo "Environment set up for running Machinekit"
fi' >> ~/.bashrc

https://docs.google.com/document/d/1GiB065ZIAaoMHPtVfTg9JV1Kn-19xGQl2X9DM9-THNM/edit


### Reading diagnostic messages
Execute the following command to find out where the latest unacknowledged message is
ethercat upload -p2 0x10f3 0x02

ethercat upload -p2 0x10f3 0x06 | hexdump -C

- Diag Code (4-byte)
- Flags (2-byte; info, warning or error)
- Text ID (2-byte; reference to explanatory text from the ESI/XML)
- Timestamp (8-byte, local slave time or 64-bit Distributed Clock time, if available)
- Dynamic parameters added by the firmware