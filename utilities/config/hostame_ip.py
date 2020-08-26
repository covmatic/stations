import argparse
import json
import logging
from typing import Optional, List, Tuple, Iterable


def system_command(cmd: str) -> str:
    return "os.system(\"{}\")".format(cmd)


def write_to_file(v: str, f: str) -> str:
    return "with open(\"{}\", \"w\") as f: f.write({})".format(f, v)


def comment(msg: str, *vars: str) -> str:
    return "robot.comment(\"{}\".format({}))".format(msg, ", ".join(vars))


class HostnameIPProtocol:
    keyfile_contents = """
# This file was placed here by Opentrons Support to work around suspected issues with mDNS.
# Normally, IP addresses are assigned dynamically by the "wired-linklocal" or "wired" connection.
# This overrides both of those to set a known, static IP address.

[connection]
id=support-team-wired-static-ip
type=ethernet
autoconnect-priority=20
interface-name=eth0
permissions=

[ethernet]
cloned-mac-address=permanent
mac-address-blacklist=

[ipv4]
dns-search=
method=manual
addresses={ip},{gateway}
dns={dns}
"""
    
    ntp_keyfile_contents = """
#  This file is part of systemd.
#
#  systemd is free software; you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 2.1 of the License, or
#  (at your option) any later version.
#
# Entries in this file show the compile time defaults.
# You can change settings by editing this file.
# Defaults can be restored by simply deleting this file.
#
# See timesyncd.conf(5) for details.

[Time]
NTP={ntp}
#FallbackNTP=time1.google.com time2.google.com time3.google.com time4.google.com
#RootDistanceMaxSec=5
#PollIntervalMinSec=32
#PollIntervalMaxSec=2048
"""
    
    def __init__(
        self,
        name: Optional[str] = None,
        hostname: Optional[str] = None,
        ip: Optional[str] = None,
        dns: Optional[Iterable[str]] = None,
        gateway: Optional[str] = None,
        ntp: Optional[str] = None,
        filepath: Optional[str] = None,
        exec_simul: bool = False,
    ):
        self.name = name
        self.hostname = hostname or (name and "CAL-LAB-{}".format(name))
        self.ip = ip and "{}/24".format(ip)
        self.dns = dns
        self.gateway = gateway
        self.ntp = ntp
        self._fp = filepath
        self.exec_simul = exec_simul
    
    @property
    def filepath(self) -> str:
        return self._fp or "hostname_ip" + ("_" + self.name.lower() if self.name else "") + "_protocol.py"
    
    def set_hostname(self) -> str:
        return "" if self.hostname is None else "echo {} > /etc/hostname".format(self.hostname)
    
    imports = "from opentrons import robot", "import os"
    
    @property
    def var_inits(self) -> List[str]:
        vlist = []
        if self.name:
            vlist.append("name = \"{}\"".format(self.name))
            vlist.append(r'machine_info = "DEPLOYMENT=production\nPRETTY_HOSTNAME={}\n".format(name)')
        if self.hostname:
            vlist.append("hostname = \"{}\"".format(self.hostname))
        if self.ip:
            vlist.append("ip = \"{}\"".format(self.ip))
        if self.dns:
            vlist.append("dns = {}".format(repr(self.dns)))
        if self.gateway:
            vlist.append("gateway = \"{}\"".format(self.gateway))
        if self.ntp:
            vlist.append("ntp = \"{}\"".format(self.ntp))
            vlist.append('ntp_keyfile = \"\"\"{}\"\"\".format(ntp=ntp)'.format(self.ntp_keyfile_contents))
        if self.ip and self.dns and self.gateway:
            vlist.append('keyfile = \"\"\"{}\"\"\".format(ip=ip, gateway=gateway, dns="".join(map({}, dns)))'.format(self.keyfile_contents, '"{};".format'))
        return vlist
    
    @property
    def commands(self) -> List[str]:
        cmds = []
        if self.name:
            cmds.append(write_to_file("machine_info", "/etc/machine-info"))
        if self.hostname:
            cmds.append(r'hostname += "\n"')
            cmds.append(write_to_file("hostname", "/var/serial"))
            cmds.append(write_to_file("hostname", "/etc/hostname"))
        if self.ntp:
            cmds.append(system_command("mount -o remount,rw /"))
            cmds.append(write_to_file("ntp_keyfile", "/etc/systemd/timesyncd.conf"))
            cmds.append(system_command("mount -o remount,ro /"))
        if self.ip and self.dns and self.gateway:
            cmds.append(write_to_file("keyfile", "/var/lib/NetworkManager/system-connections/support-team-wired-static-ip"))
        if cmds:
            cmds.append("os.sync()")
        return cmds
    
    @property
    def comments(self) -> List[Tuple[str, ...]]:
        cmts = []
        if self.name:
            cmts.append(("Setting robot's name to '{}'", "name"))
        if self.hostname:
            cmts.append(("Setting the robot's hostname to '{}'", "hostname"))
        if self.ntp:
            cmts.append(("Setting the NTP address to {}", "ntp"))
        if self.ip:
            cmts.append(("Setting the robot's IP address to {}", "ip"))
            if self.dns and self.gateway:
                cmts.append(("Setting the robot's gateway to {} and DNSs to {}", "gateway", '", ".join(dns)'))
        if cmts:
            cmts.append(("Restart your OT-2 to apply the changes",))
        return cmts
    
    def import_section(self, spacing: int = 2) -> str:
        return "\n".join(self.imports) + "\n" * spacing
    
    def init_section(self) -> str:
        return "".join(map("\n{}".format, self.var_inits))
    
    def comment_section(self) -> str:
        return "".join("\n{}".format(comment(*c)) for c in self.comments)
    
    def command_section(self, indent: int = 4) -> str:
        if not self.commands:
            return ""
        if self.exec_simul:
            return "".join(map("\n{}".format, self.commands))
        else:
            return "\nif not robot.is_simulating():" + "".join(map(("\n" + " " * indent + "{}").format, self.commands))
    
    def __str__(self) -> str:
        return self.import_section() + self.init_section() + self.comment_section() + self.command_section()
    
    def save(self):
        logging.info(" writing protocol to {}".format(self.filepath))
        with open(self.filepath, "w") as f:
            f.write(str(self))


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser(description='Configure the protocol for setting the Hostname and a Static IP address')
    parser.add_argument('-N', '--name', metavar='name', type=str, default=None, help='the desired name for the robot')
    parser.add_argument('-H', '--hostname', metavar='name', type=str, default=None, help='the desired Hostname for the robot')
    parser.add_argument('-A', '--ip-address', dest="ip", metavar='addr', type=str, default=None, help='the desired IP Address for the robot')
    parser.add_argument('-G', '--gateway', metavar='ip', type=str, default=None, help='the Gateway address')
    parser.add_argument('-D', '--dns', metavar='ip', type=str, nargs="*", default=[], help='the DNS addresses')
    parser.add_argument('-T', '--ntp', metavar='ip', type=str, default=None, help='the NTP server address')
    parser.add_argument('-O', '--output-filepath', dest="filepath", metavar='addr', type=str, default=None, help='the output file path')
    parser.add_argument('-E', '--exec-simul', action="store_true", help='let the protocol be executed during simulation')
    parser.add_argument('-q', '--quiet', action="store_true", help='quiet mode')
    parser.add_argument(dest="json_file", metavar='json file', type=str, default=None, nargs='?', help='JSON file with a list of configurations. It must contain a JSON array of objects with optional fields "name" (string), "hostname" (string), "ip" (string), "dns" (array of strings), "gateway" (string), "ntp" (string), "filepath" (str) and "exec_simul" (bool). If specified, the other parameters (except quiet mode) have no effect')
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    if args.json_file is None:
        configs = [vars(args)]
        del configs[0]['json_file']
        del configs[0]['quiet']
    else:
        with open(args.json_file, "r") as json_file:
            configs = json.load(json_file)
    
    for c in configs:
        HostnameIPProtocol(**c).save()
