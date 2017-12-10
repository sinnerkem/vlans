import os
import re
from netmiko import ConnectHandler

DIC_CISCO = 'dic_cisco.txt'
LLDP_FILE = 'lldp.txt'
OUI_FILE = 'oui.txt'
DEVICES_IP = ['172.27.8.44']
EXCLUDED = ['Gi0/8']
AUTOMATIC_WORD = 'A_'
MANUAL_WORD = 'M_'


USER = os.environ.get('SSH_USER')
PASSWORD = os.environ.get('SSH_PASSWORD')
get_mac_table = 'show mac address-table dynamic interface '
get_interfaces = 'show int status | inc connected'
get_lldp = 'show lldp neighbors'
get_interface_config = 'show run int'
get_interface_config_start = 'interface'

macs_per_port_re = re.compile('[^\d]*(\d{1,})\s{1,}.*([0-9a-f]{4,4}\.[0-9a-f]{4,4}\.[0-9a-f]{4,4}).*')
ports_re = re.compile('([A-Za-z\-]+[\/0-9]+)\s+(\S*)\s+connected.*')
mac_list = []
all_ports = []
ports = []


	
dicts_lldp = {}
dicts_oui = {}


class Port:
	def __init__(self, name, config, descr, mac_table, neighbours):
		mac_list = []
		self.unknown_macs = []
		self.name = name
		self.wrong_vlan_macs = []
		self.description = descr
		self.lldp_neighbours = neighbours # на будущее
		self.configuration = config # на будущее
		self.macs = 0
		mac_table_lines = mac_table.splitlines()
		for i in  mac_table_lines:
			str = re.match(macs_per_port_re,i)
			if str != None:
				mac_list.append(str.groups())
		self.macs = len(mac_list)
		
		for i in mac_list:
			key = 0
			for j in dicts_oui.keys():
				if j in i[1]:
					key = 1
					if dicts_oui.get(j) != i[0]:
						(self.wrong_vlan_macs).append(i)
			if key ==0:
				(self.unknown_macs).append(i)

# создаем словарь соотвествия коротких имен интерфесов и длинных
with open(DIC_CISCO,'r') as inf:
	for line in inf:
		(key, val) = line.split(',')
		dicts_int_shortname[key.strip()] = val.strip()


# создаем словарь lldp
with open(LLDP_FILE,'r') as inf:
        for line in inf:
                (key, val) = line.split(',')
                dicts_lldp[key.strip()] = val.strip()

with open(OUI_FILE,'r') as inf:
        for line in inf:
                (key, val) = line.split(',')
                dicts_oui[key.strip()] = val.strip()



for IP in DEVICES_IP:
	print('Connection to device {}'.format(IP))
	DEVICE_PARAMS = {'device_type': 'cisco_ios',
		'ip': IP,
		'username': USER,
		'password': PASSWORD
	}
	with ConnectHandler(**DEVICE_PARAMS) as ssh:
		print( ssh.find_prompt())
		ssh.enable()
					
		for i in (ssh.send_command(get_interfaces)).splitlines():
			str = re.match(ports_re,i)
			if str != None:
				if  (str.groups())[0] not in EXCLUDED:
					all_ports.append([(str.groups())[0],(str.groups())[1]])

		for index,i in enumerate(all_ports):
			lldp_neighbor = ssh.send_command(get_lldp+' '+i[0]+' detail')
			all_ports[index].append(lldp_neighbor)
			
			mac_table = ssh.send_command(get_mac_table+i[0])
			
			interface_config = ssh.send_command(get_interface_config+' '+i[0]+' | begin '+get_interface_config_start)
			all_ports[index].append(interface_config)
			ports.append(Port(all_ports[index][0],interface_config, all_ports[index][1], mac_table, lldp_neighbor))
			
		for index,i in enumerate(ports):
			print(i.name)
			if (i.description).startswith(AUTOMATIC_WORD) == True:
				if len(i.wrong_vlan_macs) != 0:
					print('wrong_vlan_macs:')
					print (i.wrong_vlan_macs)
				if len(i.unknown_macs) != 0:
					print('unknown_macs:')	
					print (i.unknown_macs)

			elif (i.description).startswith(MANUAL_WORD) == True:
				print(MANUAL_WORD)
				if len(i.wrong_vlan_macs) != 0:
					print('wrong_vlan_macs:')
					print(i.wrong_vlan_macs)
				
			else:
				print('NoneDesc')
				if len(i.wrong_vlan_macs) != 0:
					print('wrong_vlan_macs:')
					print (i.wrong_vlan_macs)
				if len(i.unknown_macs) != 0:
					print('unknown_macs:')
					print (i.unknown_macs)



# получаем список портов на комму
#ports = [row[2] for row in mac_list]


#macs_per_port = dict((i, ports.count(i)) for i in ports)

#mac_list[:] = [i for i in mac_list if  macs_per_port.get(i[2]) == 1]
#print(mac_list)
