
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


class AwsAccount(models.Model):
    '''
    Amazon Web Service Account
    '''
    account_number = models.PositiveIntegerField(primary_key = True)
    access_key     = models.CharField(max_length = 255)
    secret_key     = models.CharField(max_length = 255)
    prefix         = models.CharField(max_length = 255)
    
    def __unicode__(self):
        return u'%s' % self.account_number
    
    def spot_price_bucket(self, bucket_name = 'spot-price-bucket'):
        return get_or_create_bucket(s3(self),('%s-%s' % (self.prefix,bucket_name)).lower())


class AMI(models.Model):
    '''
    Amazon Machine Image
    It is own by one account
    '''
    id               = models.CharField(primary_key = True, max_length = 255)
    name             = models.CharField(max_length = 255)
    root_device_type = models.PositiveIntegerField(choices = rdtypes,
                                                   verbose_name = 'Root Device Type')
    root_device_name = models.CharField(max_length = 255)
    account          = models.ForeignKey(AwsAccount)
    platform         = models.CharField(max_length = 255)
    architecture     = models.CharField(max_length = 255)
    is_public        = models.BooleanField(default = False)
    
    def __unicode__(self):
        return u'Image: %s' % self.id
    
    def image(self):
        '''
        Return a boto Image object coreespoinding to the model instance
        '''
        c           = ec2(self.account)
        return c.get_image(self.id)
    
    def run(self):
        image       = self.image()
        reservation = self
    
    
class Instances(models.Model):
    id               = models.CharField(primary_key = True, max_length = 255)
    ami              = models.ForeignKey(AMI)
    
    
    

