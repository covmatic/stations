# Hostname and IP configuration
The script [`hostname_ip.py`](hostname_ip.py) can be used to generate setup protocols for your OT-2 robot.

## Parameters
It accepts the following parameters
- `-N name, --name name`  
  the desired name for the robot. If specified, set the display name to this name
- `-H name, --hostname name`  
  the desired Hostname for the robot. If specified, set the hostname to this name. Otherwise, if `--name` is given, set the hostname the same as that name 
- `-A addr, --ip-address addr`  
  the desired IP Address for the robot. If `--gateway` and `--dns` are also given, set the robot's default wired IP address, gateway address and DNS address(es)
- `-G ip, --gateway ip`  
  the Gateway address.  If `--ip-address` and `--dns` are also given, set the robot's default wired IP address, gateway address and DNS address(es)
- `-D [ip [ip ...]], --dns [ip [ip ...]]`  
  the DNS addresses.  If `--gateway` and `--ip-address` are also given, set the robot's default wired IP address, gateway address and DNS address(es)
- `-T ip, --ntp ip`  
  the NTP server address. If specified, set the NTP server address to this address.
- `-O addr, --output-filepath addr`  
  the output file path. If not specified, the protocol files are generated in the working directory

## Configuration file
You can store a list of configurations in a JSON file and give as the JSON file path as the only argument to the script
```
python hostame_ip.py json file
```
The JSON file must be a list of objects.
One configuration protocol will be generated for each object.
Supported keys are
- name
- hostname
- ip
- gateway
- dns
- ntp
- filepath

For a detailed description refer to the section [*parameters*](#parameters)
