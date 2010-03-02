import os
import stat
from django.db import models
from django.utils.translation import ugettext_lazy as _

from amazoncloud.core import installers
from amazoncloud.settings import EBS_COST_GB_MONTH


def s3(account):
    from boto.s3.connection import S3Connection
    return S3Connection(str(account.access_key),str(account.secret_key))

def get_or_create_bucket(conn,name):
    try:
        conn.get_bucket(name)
    except:
        return conn.create_bucket(name)

def ec2(account):
    from boto.ec2.connection import EC2Connection
    return EC2Connection(str(account.access_key),str(account.secret_key))


rdtypes = ((0, 'unknown'),
           (1, 'ebs'),
           (2, 'instance-store')
           )
rddict = dict(rdtypes)

archtype = (('i386','i386'),
            ('x86_64','x86_64')
            )
instype = (('m1.small','Sm1.small (1.7 GB)'),
           ('c1.medium','c1.medium (7.5 GB)')
           )
supported_os = (('ubuntu','ubuntu'),
                ('windows','windows'),
                )


class AwsAccount(models.Model):
    '''
    Amazon Web Service Account
    '''
    id           = models.CharField(max_length = 255, primary_key = True)
    access_key   = models.CharField(max_length = 255)
    secret_key   = models.CharField(max_length = 255)
    prefix       = models.CharField(max_length = 255,
                                      help_text = 'This is used as a prefix when creating S3 buckets')
    
    def __unicode__(self):
        return u'{0}: {1}'.format(self.prefix,self.id)
    
    def spot_price_bucket(self, bucket_name = 'spot-price-bucket'):
        return get_or_create_bucket(s3(self),('%s-%s' % (self.prefix,bucket_name)).lower())
    
    def ec2(self):
        return ec2(self)
    
    def allocate_address(self):
        '''
        Allocate new IP address
        '''
        return self.ec2().allocate_address()


class EC2base(models.Model):    
    class Meta:
        abstract = True
        
    def ec2(self):
        return ec2(self.account)

    
class SecurityGroup(EC2base):
    name    = models.CharField(max_length = 255)
    account = models.ForeignKey(AwsAccount, related_name = 'security_groups')
    
    def __unicode__(self):
        return u'{0}'.format(self.name)
    
    class Meta:
        unique_together = ('name','account')
        
class KeyPair(EC2base):
    name         = models.CharField(max_length = 255)
    fingerprint  = models.CharField(max_length = 255, editable = False)
    account      = models.ForeignKey(AwsAccount, related_name = 'keypairs')
    material     = models.TextField(blank = True)
    
    class Meta:
        unique_together = ('name','account')
        
    def __unicode__(self):
        return u'{0}'.format(self.name)
    
    def key_filename(self):
        from amazoncloud.settings import SSH_KEYS_PATH
        if SSH_KEYS_PATH and self.material:
            return os.path.join(SSH_KEYS_PATH,'{0}.pem'.format(self.name)) 
        
    def dump(self):
        '''
        Dump material into file if available
        '''
        path = self.key_filename()
        if path and self.material:
            if os.path.isfile(path):
                os.chmod(path, stat.S_IWUSR)
            f = open(path,'w')
            f.write(self.material)
            f.close()
            os.chmod(path, stat.S_IRUSR)


class AMI(EC2base):
    '''
    Amazon Machine Image - slightly denormalized
    '''
    id               = models.CharField(primary_key = True, max_length = 255, editable = False)
    timestamp        = models.DateTimeField(auto_now_add = True, editable = False)
    name             = models.CharField(max_length = 255)
    description      = models.TextField(blank = True)
    root_device_type = models.PositiveIntegerField(choices = rdtypes,
                                                   verbose_name = 'Root Device Type')
    location         = models.CharField(max_length = 255)
    root_device_name = models.CharField(max_length = 255)
    account          = models.ForeignKey(AwsAccount, null = True, blank = True)
    owner_id         = models.CharField(max_length = 255)
    platform         = models.CharField(choices = supported_os, max_length = 255, blank = True)
    architecture     = models.CharField(choices = archtype, max_length = 255)
    is_public        = models.BooleanField(default = False)
    kernel_id        = models.CharField(max_length = 255)
    region           = models.CharField(max_length = 64)
    snapshot_id      = models.CharField(max_length = 64)
    size             = models.PositiveIntegerField(default = 0)
    our              = models.BooleanField()
    
    class Meta:
        verbose_name = 'AMI'
        verbose_name_plural = 'AMIs'
        
    def __unicode__(self):
        return u'Image: %s' % self.id
    
    def cost(self):
        '''
        Estimated cost/month
        '''
        if self.our and self.root_device_type == 1:
            return EBS_COST_GB_MONTH*self.size
        else:
            return 0
    cost.short_description = 'cost ($)'
    
    def boto(self):
        '''
        Return a boto Image object coreespoinding to the model instance
        '''
        if self.account:
            c = ec2(self.account)
            return c.get_image(self.id)
    
    def run(self):
        image       = self.image()
        reservation = self
        
    def accno(self):
        if self.account:
            return self.account
        else:
            return self.owner_id
        
    #def our(self):
    #    return self.account is not None
    #our.boolean = True
    
    
class Instance(EC2base):
    id      = models.CharField(primary_key = True, max_length = 255, editable = False)
    account = models.ForeignKey(AwsAccount)
    ami     = models.ForeignKey(AMI)
    state   = models.CharField(max_length = 255, editable = False)
    timestamp = models.DateTimeField(editable = False, null = True, verbose_name = _('started'))
    type   = models.CharField(choices = instype, max_length = 255)
    size    = models.PositiveIntegerField(default = 0)
    private_dns_name = models.CharField(max_length = 500, editable = False, blank = True)
    public_dns_name = models.CharField(max_length = 500, editable = False, blank = True)
    ip_address = models.CharField(max_length = 32, blank = True)
    monitored = models.BooleanField(default = False)
    region    = models.CharField(max_length = 255, blank = True)
    key_pair  = models.ForeignKey(KeyPair)
    security_groups = models.ManyToManyField(SecurityGroup, null = True)
    
    def __unicode__(self):
        return u'Instance: %s' % self.id
    
    def instance(self):
        '''
        Return a boto Image object correspoinding to the model instance
        '''
        c = self.ec2()
        re = c.get_all_instances([self.id])
        try:
            return re[0].instances[0]
        except:
            return None
    
    def root(self):
        return rddict.get(self.ami.root_device_type)
    
    def sgroup(self):
        return [s.name for s in self.security_groups.all()]
    
    def security(self):
        return ', '.join(self.sgroup())
    security.short_description = 'security groups'
    
    def cost(self):
        '''
        Estimated cost/month
        '''
        return 0
    cost.short_description = 'cost ($)'
    

class IpAddress(EC2base):
    account = models.ForeignKey(AwsAccount)
    ip = models.IPAddressField(unique = True)
    instance = models.ForeignKey(Instance, null = True)    

    
class Installer(models.Model):
    name     = models.CharField(unique = True, max_length = 255)
    packages = models.TextField(blank = True)
    osystem  = models.CharField(choices = supported_os, max_length = 64, verbose_name = 'operative system')
    
    def __unicode__(self):
        return u'%s' % self.name
    
    def install(self, instance):
        f = getattr(installers,self.osystem, None)
        if f:
            f(instance, self.packages)

        
    
    
    

