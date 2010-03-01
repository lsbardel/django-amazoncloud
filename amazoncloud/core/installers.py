
from fabric.api import *



def fabinstall(instance, command):
    env.key_filename = instance.key_pair.key_filename()
    sudo(command)




def ubuntu(self, instance, packages):
    packages = self.instance.ami.packages
    if packages:
        command   = 'apt-get -y install %s' % packages
        url       = instance.public_dns_name
        env.user  = 'ubuntu'
        fabinstall(instance,command)
        