
from fabric.api import *


# sudo dpkg -i webmin_1.500_all.deb
# to install missing dependencies
# sudo apt-get install -f


def fabinstall(instance, command):
    env.key_filename = instance.key_pair.key_filename()
    sudo(command)




def ubuntu(instance, packages):
    commands = packages.split('\r\n')
    for command in commands:
        env.host_string = instance.public_dns_name
        env.virtualhost_path = "/"
        env.user  = 'ubuntu'
        fabinstall(instance,command)
        