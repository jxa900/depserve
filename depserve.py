# build something to align:

# DHCP entries for management network (VLAN 22)
# /var/lib/tftboot/pxelinux.cfg symlinks so that
# we can reliably change things from deploy to not

# one dandy technique is to put the kickstart behind
# a flask server, then change the symlink on
# http GET. This means it will only deploy once.

# (a pain to test though)

import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

class Host():
    def __init__(self, name, mac, ip):
        self.name = name
        self.mac = mac
        self.ip = ip 
        self.install = "" 

    def __repr__(self):
        return "Host " + self.name + " mac: " + self.mac + " ip: " + self.ip
        
def build_host_list():
    hosts = list()

    dhcpconf = open('/etc/dhcp3/dhcpd.conf', 'r')

    # testing paren blocks
    th = list()

    names = list()
    macs = list()
    ips = list()

    f = file.read(dhcpconf).split('}')
    for e in f:
        if len(e) < 300: # arbitrary number that should be big enough
            th.append(e)

    for host in th:
        for element in host.split('\n'):
            if ';' in element:
                if 'server-name' in element:
                    names.append(element.split('"')[-2])
                if 'hardware' in element:
                    macs.append(element.split(' ')[-1][:-1]) 
                if 'address' in element:    
                    ips.append(element.split(' ')[-1][:-1]) 
                    
    for i in range(len(names)):
        hosts.append(Host(names[i], macs[i], ips[i]))

    ls = os.listdir('/var/lib/tftpboot/pxelinux.cfg')
    for host in hosts:
        for link in ls:
            if '01-' + host.mac.replace(':', '-').lower() == link:
                with open('/var/lib/tftpboot/pxelinux.cfg/01-' + host.mac.replace(':', '-').lower(), 'r') as linkedfile:
                    host.install = linkedfile.readlines()[0][:-2]
    return hosts

def create_link(bootfile, hosts):
    for host in hosts:
         try: 
             os.remove('/var/lib/tftpboot/pxelinux.cfg/01-' + host.mac.replace(':', '-').lower())
         except:
             pass
         os.symlink(bootfile, '/var/lib/tftpboot/pxelinux.cfg/01-' + host.mac.replace(':', '-').lower())

@app.route('/kickstart')
def kickstart():
    ip = request.remote_addr
    hosts = build_host_list()
    host = [h for h in hosts if h.ip == ip]
    if len(host) == 0:
        return render_template('terrible_plan.html')
        
    create_link('ubuntu', host)    
    return render_template('kickstart.html', name = host[0].name)

@app.route('/info')
def kickstart():
    hosts = build_host_list()
    return render_template('info.html', hosts = hosts)

@app.route('/hostname')
def hostname():
    ip = request.remote_addr
    hosts = build_host_list()
    host = [h for h in hosts if h.ip == ip]
    if len(host) == 0:
        return render_template('terrible_plan.html')
    return render_template('hostname', name = host[0].name)    
        
    create_link('ubuntu', host)    
    return render_template('kickstart.html')

@app.route('/reset')
def installer():
    hosts = build_host_list()
    #create_link('ubuntu', hosts)
    ceph = [host for host in hosts if 'ceph' in host.name]
    # last two are being used by Openstack prod.
    ch4 =  [host for host in hosts if ('stack-04' in host.name and '0415' not in host.name and '0416' not in host.name)]
    create_link('install', ceph)
    create_link('install', ch4)
    return render_template('terrible_plan.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0',  debug=True)
