

class ubuntu(system.base):

    def __init__(self, instance):
        self.instance = instance
        
    def install(self):
        packages = self.instance.ami.packages
        if packages:
            packages = 'apt-get -y install %s' % packages
        
        
        