
from django.db import models


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

instype = (('m1.small','m1.small (1.7 GB)'),
           ('c1.medium','c1.medium')
           )


class AwsAccount(models.Model):
    '''
    Amazon Web Service Account
    '''
    account_number = models.CharField(max_length = 255, primary_key = True)
    access_key     = models.CharField(max_length = 255)
    secret_key     = models.CharField(max_length = 255)
    prefix         = models.CharField(max_length = 255,
                                      help_text = 'This is used as a prefix when creating S3 buckets')
    
    def __unicode__(self):
        return u'{0}: {1}'.format(self.prefix,self.account_number)
    
    def spot_price_bucket(self, bucket_name = 'spot-price-bucket'):
        return get_or_create_bucket(s3(self),('%s-%s' % (self.prefix,bucket_name)).lower())
    
class SecurityGroup(models.Model):
    name    = models.CharField(max_length = 255)
    account = models.ForeignKey(AwsAccount, related_name = 'security_groups')
    
    def __unicode__(self):
        return u'{0}'.format(self.name)
    
    class Meta:
        unique_together = ('name','account')
        
class KeyPair(models.Model):
    name    = models.CharField(max_length = 255)
    fingerprint  = models.CharField(max_length = 255)
    account = models.ForeignKey(AwsAccount, related_name = 'keypairs')
    
    def __unicode__(self):
        return u'{0}'.format(self.name)
    
    class Meta:
        unique_together = ('name','account')



class EC2base(models.Model):
    id      = models.CharField(primary_key = True, max_length = 255, editable = False)
    
    class Meta:
        abstract = True
        
    def ec2(self):
        return ec2(self.account)


class AMI(EC2base):
    '''
    Amazon Machine Image - slightly denormalized
    '''
    timestamp        = models.DateTimeField(auto_now_add = True, editable = False)
    name             = models.CharField(max_length = 255)
    description      = models.TextField()
    root_device_type = models.PositiveIntegerField(choices = rdtypes,
                                                   verbose_name = 'Root Device Type')
    location         = models.CharField(max_length = 255)
    root_device_name = models.CharField(max_length = 255)
    account          = models.ForeignKey(AwsAccount, null = True, blank = True)
    owner_id         = models.CharField(max_length = 255)
    platform         = models.CharField(max_length = 255)
    architecture     = models.CharField(max_length = 255)
    is_public        = models.BooleanField(default = False)
    kernel_id        = models.CharField(max_length = 255)
    region           = models.CharField(max_length = 64)
    snapshot_id      = models.CharField(max_length = 64)
    size             = models.FloatField(default = 0)
    our              = models.BooleanField()
    
    class Meta:
        verbose_name = 'AMI'
        verbose_name_plural = 'AMIs'
        
    def __unicode__(self):
        return u'Image: %s' % self.id
    
    def image(self):
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
    account = models.ForeignKey(AwsAccount)
    ami     = models.ForeignKey(AMI)
    state   = models.CharField(max_length = 255, editable = False)
    timestamp = models.DateTimeField(editable = False, null = True)
    type   = models.CharField(choices = instype, max_length = 255)
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
        account = self.ami.account
        if account:
            c  = ec2(self.account)
            return c.get_instance(self.id)
    
    def root(self):
        return rddict.get(self.ami.root_device_type)
    
    def sgroup(self):
        return [s.name for s in self.security_groups.all()]
    
    def security(self):
        return ', '.join(self.sgroup())
    security.short_description = 'security groups'
        
        
    
    
    

