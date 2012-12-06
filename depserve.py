"""
Depserve
--------

A deployment server written using the flask framework. Kickstarts are sent out only to ip adresses present in the dhcpd.conf file. Symlinks to change PXE boot behavior between booting from local disk and installing from ubuntu mirror are maintained. Each time a host pulls down a kickstart, the symlink is changed to localboot.
"""
import os
from flask import Flask, render_template, request, jsonify
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

dhcp_path = '/etc/dhcp3/dhcpd.conf'
pxe_path = '/var/lib/tftpboot/pxelinux.cfg'

#dhcp_path = './testing/dhcpd.conf'
#pxe_path = './testing/pxe'

class Host():
    """ A single server (VM or otherwise) with an entry in the dhcpd.conf file. """
    def __init__(self, name, mac, ip):
        self.name = name
        self.mac = mac
        self.ip = ip 
        self.install = "" 

    def __repr__(self):
        return "Host " + self.name + " mac: " + self.mac + " ip: " + self.ip

""" Parses the dhcpd.conf file and returns a list of hosts, which
contains the server name, mac, ip and whether it's going to install 
on boot """
def build_host_list():
    hosts = list()

    dhcpconf = open(dhcp_path, 'r')

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

    ls = os.listdir(pxe_path)
    for host in hosts:
        for link in ls:
            if '01-' + host.mac.replace(':', '-').lower() == link:
                with open(pxe_path + '/01-' + host.mac.replace(':', '-').lower(), 'r') as linkedfile:
                    host.install = linkedfile.readlines()[0][:-2]
    return hosts

""" Removes existing symlink and replaces it with the specified one """
def create_link(bootfile, hosts):
    for host in hosts:
         try: 
             os.remove(pxe_path + '/01-' + host.mac.replace(':', '-').lower())
         except:
             pass
         os.symlink(bootfile, pxe_path + '/01-' + host.mac.replace(':', '-').lower())

""" Returns the hostname for the node """
@app.route('/hostname')
def hostname():
    ip = request.remote_addr
    hosts = build_host_list()
    host = [h for h in hosts if h.ip == ip]

    if len(host) != 0:
        host = host[0]
    else:
        return render_template('terrible_plan.html')
    return render_template('hostname', name=host.name)    


""" Route for machines to hit when they require a kickstart. This is specified in the install
file under pxelinux.cfg. Returns a kickstart file  """
@app.route('/kickstart')
def kickstart():
    ip = request.remote_addr
    hosts = build_host_list()
    #print hosts
    host = [h for h in hosts if h.ip == ip]
    print host
    if len(host) == 0:
        print "onoes"
        return render_template('terrible_plan.html')

    create_link('ubuntu', host)

    with open('rootpw', 'r') as pwfile:
        pw = pwfile.readlines()[0]

    return render_template('kickstart.html', pw=pw)

""" Route for status queries. TODO Return JSON """
@app.route('/info')
def info():
    hosts = build_host_list()
    return render_template('info.html', hosts = hosts)

""" Testing route that sets hosts to install """ 
@app.route('/reset')
def installer():
    hosts = build_host_list()
    #create_link('ubuntu', hosts)
    # last two are being used by Openstack Essex prod.
    ch4 =  [host for host in hosts if ('stack-04' in host.name and '0415' not in host.name and '0416' not in host.name)]
    create_link('install', ch4)
    return render_template('terrible_plan.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
