# Machinekit Experiments - Beaglebone Black with Beckhoff EL7201
## Summary

This readme covers the steps I am taking to get an EL7201 servo motor driver to work with a Beaglebone Black. This project is mostly about learning EtherCAT and determining how much effort is required to drive a servo motor from a Linux PC.

## Hardware

- Controller
  - Beaglebone Black (ELEMENT14 BBONE-BLACK-4G BEAGLEBONE BLACK REV C, CORTEX A8)
- Memory Card
  - Sandisk Ultra 64GB Micro SDXC UHS-I Card (SDSQUAR-064G-GN6MA)
- EtherCAT rack
  - EK1101 EtherCAT Coupler
  - EL2624 (not used)
  - EL7201 Servomotor terminal for resolver, 50 V DC, 2.8 ARMS
    - AM8111-0F10-0000 Servo Motor

## Setup the Beaglebone Black

Download `bone-debian-9.5-lxqt-armhf-2018-10-07-4gb.img.xz` or the latest armhf image from the Beaglebone website and follow the instructions on http://beagleboard.org/getting-started to flash the image to the SD card using the Etcher tool.

With power off to the BBB, insert the SD card. Provide power to the BBB. The board should automatically boot from the SD card since the Etcher tool makes a bootable drive.

Wait for Windows (or Linux) to recognize the BBB as a network device. Login to the board with ssh (password `temppwd`):

    ssh debian@192.168.7.2

### Expand the drive

Follow the steps on https://elinux.org/Beagleboard:Expanding_File_System_Partition_On_A_microSD to expand the partition so that you have access to the full size of the SD card.

### Add a swap partition

In later steps I ran out of memory when trying to build from sources using gcc. I added a swap partition which solved this. Follow the instructions on https://digitizor.com/create-swap-file-ubuntu-linux/.

### Setup internet connection using the USB adapter

Setup an internet connection to the Beaglebone Black following the instructions from https://www.digikey.com/en/maker/blogs/how-to-connect-a-beaglebone-black-to-the-internet-using-usb.

#### Instructions for Windows

From Network Connections in Windows, find the network connection you are using to get internet. In my case it was the wireless adapter.

Go to Properties > Sharing, and enable Sharing. Select the USB Network Adapter which was created when you plugged in the Beaglebone.

There will be a prompt about changing the IP address, you can click OK.

Now go the BBB USB Network Adapter, change the IP address to `192.168.7.1`, the subnet mask to `255.255.255.0` and the Preferred DNS server to `8.8.8.8`

Login to the board again with ssh

Enter root

    sudo su

Execute the following commands
    
    /sbin/route add default gw 192.168.7.1
    echo "nameserver 8.8.8.8" >> /etc/resolv.conf

Now you should be able to ping google

    ping google.com

### Log in and create the machinekit user

The following steps were derived from https://machinekoder.com/machinekit-debian-stretch-beaglebone-black/

Log in via SSH with the username debian and password temppwd.

    ssh debian@192.168.7.2

Create the machinekit user, make sure to remember the password

    sudo su
    adduser machinekit

Setup permissions for the new user and make it so that no password is required for sudo access

    usermod -aG  sudo,kmem,netdev,video machinekit
    echo -e "# No sudo password for machinekit user\nmachinekit ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/90-machinekit
    exit

Then log out from the SSH shell with exit.

Now you could delete the original user (I didn't do this step).

### Install requirements

    sudo apt update
    sudo apt upgrade
    sudo apt install -y avahi-daemon network-manager nano git usbutils dirmngr locales firmware-misc-nonfree \
        libnotify-bin iw dnsmasq apt-offline zip unzip \
        libprotobuf-c0-dev protobuf-c-compiler libjpeg-dev python-smbus make python-setuptools python-dev gcc python-zmq libzmq3-dev \
        libzmq3-dev libprotobuf-dev


### Install the RT Kernel

Now it’s time to install the PREEMPT_RT kernel on our system.

For this, we can use the prepared scripts.

    cd /opt/scripts/tools/
    sudo su
    git pull
    ./update_kernel.sh --ti-rt-channel --lts-4_4

Once the installation is complete, reboot the system and run the following command to install additional firmware packages.

sudo apt install linux-firmware-image-`uname -r`

In my case this command returned:
> Linux beaglebone 4.1.15-ti-rt-r43 #1 SMP PREEMPT RT Thu Jan 21 20:13:58 UTC 2016  armv7l GNU/Linux

### Install machinekit from sources
At this point I was trying to follow the instructions from https://github.com/koppi/mk/blob/master/Machinekit-RT-Preempt-RPI.md, but I was having trouble with locating the machinekit-dev package, so I built and installed it from source following these instructions: http://www.machinekit.io/docs/developing/machinekit-developing/

This step took almost four hours, I am not sure if it was an issue with disk write speed or memory limitations of the BBB. I believe you can build this in a docker container using the machinekit tools (on a separate PC), which I will try if I have to build it again.

#### Add the machinekit repository
Add the machinekit repository for your distribution (see http://www.machinekit.io/docs/getting-started/installing-packages/#configure-apt), in my case I am using Debian Stretch:

    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 43DDF224
    sudo sh -c \
    "echo 'deb http://deb.machinekit.io/debian stretch main' > \
    /etc/apt/sources.list.d/machinekit.list"
    sudo apt-get update

#### Install development requirements

    sudo apt-get install libczmq-dev python-zmq libjansson-dev pkg-config \
    libwebsockets-dev python-pyftpdlib cython bwidget lsb-release
    
#### Get and build the source

    sudo apt-get install git dpkg-dev
    sudo apt-get install --no-install-recommends devscripts equivs
    git clone https://github.com/machinekit/machinekit.git
    cd machinekit

    # to add RT-PREEMPT support, add a 'r'
    debian/configure -r
    sudo mk-build-deps -ir
    cd src
    ./autogen.sh
    ./configure --with-platform-beaglebone 
    make
    sudo make setuid

    # this script checks for missing configuration files
    # and will give hints how to remedy:
    ../scripts/check-system-configuration.sh

Run the following command to add the command to source this environment by default when launching bash (this will make machinekit available as a command and is also necessary for the step where we install LinuxCNC-EtherCAT support).

    echo 'if [ -f ~/machinekit/scripts/rip-environment ]; then
        source ~/machinekit/scripts/rip-environment
        echo "Environment set up for running Machinekit"
    fi' >> ~/.bashrc

Activate this environment either by logging out and back in, or running the source script manually.

    source ~/machinekit/scripts/rip-environment

### Install Etherlab support
I installed the EtherCAT master from source because the packages in APT don't work on newer Kernel versions.

Install mercurial

    sudo apt install mercurial

Clone the ethercat master

    hg clone http://hg.code.sf.net/p/etherlabmaster/code ethercat-hg
    cd ethercat-hg

Get the latest code

    hg up tip

Build from sources following the instructions in the `INSTALL` file https://sourceforge.net/p/etherlabmaster/code/ci/default/tree/INSTALL.

    ./boostrap # to create the configure script, if downloaded from the repo
    ./configure
    make all modules

Switch to root and install the modules

    sudo su
    make modules_install install
    depmod

Link the init script and copy the sysconfig file from $PREFIX/etc
to the appropriate locations and customizing the sysconfig file. Note that $PREFIX is where you installed etherlab, normally this is `/opt/etherlab`.

    ln -s ${PREFIX}/etc/init.d/ethercat /etc/init.d/ethercat

    # if the sysconfig directory doesn't exist, create it
    mkdir /etc/sysconfig

    cp ${PREFIX}/etc/sysconfig/ethercat /etc/sysconfig/ethercat

Setup the the ethercat configuration to match your device. First get the MAC address from the Beaglebone network adapter

    ifconfig

Copy the MAC address and paste into the `/etc/sysconfig/ethercat` file under the MASTER0_DEVICE. Also, set the DEVICE_MODULES to "generic".

    vi /etc/sysconfig/ethercat

For example, in my case the file looked like

    ...
    MASTER0_DEVICE="74:e1:82:86:95:be"
    ...
    DEVICE_MODULES="generic"
    ...

Make sure, that the 'udev' package is installed, to automatically create the
EtherCAT character devices. The character devices will be created with mode
0660 and group root by default. If you want to give normal users reading
access, create a udev rule like this:

    echo KERNEL==\"EtherCAT[0-9]*\", MODE=\"0664\" > /etc/udev/rules.d/99-EtherCAT.rules

Now you can start the EtherCAT master:

    /etc/init.d/ethercat start

At this point, I think something had gone wrong with the etherlab install because not all files were copied correctly to /opt/etherlab. Running `sudo make install` again seemed to fix the issue.

    cd ethercat-hg
    sudo make install

Make a symlink to the ethercat utility

    sudo ln -s /usr/bin/ethercat /opt/etherlab/bin/ethercat

Now connect a network cable between the EK1101 and the Beaglebone Black NIC and power on the ethercat slaves. Run the following command to see if the EtherCAT driver is working.

    ethercat slaves

You should see something like 

    machinekit@beaglebone:~$ ethercat slaves
    0  0:0  PREOP  +  EK1101 EtherCAT Coupler (2A E-Bus, ID switch)
    1  0:1  PREOP  +  EL2624 4K. Relais Ausgang, Schlie�er (125V AC / 30V DC)
    2  0:2  PREOP  +  EL7201-9014 1K. MDP742 Servo-Motor-Endstufe mit OCT (50V, 2,8A

### Install LinuxCNC-EtherCAT support

Clone the linuxcnc source code. I merged changes from the zultron fork which had some fixes to the makefile, and I also added EL7201 as a new module (which was easy since EL7211 is almost identical).

    git clone https://github.com/dfreiberger/linuxcnc-ethercat.git

Build and install the library

    make
    sudo make install

## Setup for EtherCAT slaves
At this point I followed the instructions on https://docs.google.com/document/d/1GiB065ZIAaoMHPtVfTg9JV1Kn-19xGQl2X9DM9-THNM/edit which showed how to create the ethercat configuration file for a slave. I was able to create a slave configuration for the EL7201 using the "generic" entry, but then I discovered that there was an EL7211 C module, so I modified linuxcnc-ethercat to add support for EL7201, since they have identical commands (the only difference is the part ID in el7201.h). See https://github.com/dfreiberger/linuxcnc-ethercat/blob/master/src/lcec_el7201.c.

The final configuration looks like. I took the motor configuration (MDP) from https://download.beckhoff.com/download/config/drives/EL72x1.

```xml
<masters>
<master idx="0" appTimePeriod="1000000" refClockSyncCycles="10">
    <slave idx="0" type="EK1100"/>
    <slave idx="1" type="generic" vid="00000002" pid="A403052" name="abc" />
    <slave idx="2" type="EL7201" name="x">
    <initCmds filename="AM8111-xFx0-000x_MDP.xml"/>
        <dcConf assignActivate="700" sync0Cycle="*1" sync0Shift="30000" sync1Cycle="*1" sync1Shift="-1000"/>
        <watchdog divider="2498" intervals="1000"/>
    </slave>
</master>
</masters>
```

I set the dcConf from the EL7201 file found in `"C:\TwinCAT\3.1\Config\Io\EtherCAT\Beckhoff EL72xx.xml"` or from https://www.beckhoff.com/english.asp?download/elconfg.htm. I am not sure if this is 100% correct yet, but it is working for me.

```xml
<Dc>
    <OpMode>
        <Name>DC</Name>
        <Desc>DC-Synchron</Desc>
        <AssignActivate>#x700</AssignActivate>
        <CycleTimeSync0 Factor="1">0</CycleTimeSync0>
        <ShiftTimeSync0 Input="0">30000</ShiftTimeSync0>
        <CycleTimeSync1 Factor="-1">0</CycleTimeSync1>
        <ShiftTimeSync1>1000</ShiftTimeSync1>
    </OpMode>
</Dc>
```

To test this configuration

    git clone https://github.com/dfreiberger/mk_experiments.git
    cd mk_experiments/bbb_1axis
    
    # start the realtime and enable the drive
    realtime start
    halcmd -f el7201.hal
    halcmd setp lcec.0.x.enable 1

    # give the motor a velocity command
    halcmd setp lcec.0.x.velo-cmd 1.

At this point I had a lot of trouble getting the motor to actually turn. Things I did that helped:

Power cycle the ethercat slaves. Do this any time you change the motor configuration or if the drive has a red Error light on it.

You can confirm that the velocity command is being written to the drive, and read other registers, with the `ethercat upload` command.

With a scaling factor of 1 `halcmd getp lcec.0.x.scale`, a velocity command of 1 `halcmd setp lcec.0.x.velo-cmd 1.`. will equal the value in the velocity encoder resolution register.

    halcmd setp lcec.0.x.velo-cmd 1.
    ethercat upload -p2 0x7010 0x06 -t int32
    # > 0x00041893 268435
    ethercat upload -p2 0x9010 0x14 -t uint32
    # > 0x00041893 268435

### Reading diagnostic messages

Execute the following command to find out where the latest unacknowledged message is

    ethercat upload -p2 0x10f3 0x02

Print out the message at that register. In this case it was at 0x06.

    ethercat upload -p2 0x10f3 0x06 | hexdump -C

The message can be decoded as described in the Beckhoff documentation. Note that the data is stored in little endian format. (See https://download.beckhoff.com/download/document/io/ethercat-terminals/el72x1en.pdf, section 9.1, page 168)

- Diag Code (4-byte)
- Flags (2-byte; info, warning or error)
- Text ID (2-byte; reference to explanatory text from the ESI/XML)
- Timestamp (8-byte, local slave time or 64-bit Distributed Clock time, if available)
- Dynamic parameters added by the firmware
