
from amazoncloud.models import AwsAccount, AMI, rddict, ec2


def rdinv():
    d = {}
    for k,v in rddict.items():
        d[v] = k
    return d

#id               = models.CharField(primary_key = True, max_length = 255)
#    name             = models.CharField(max_length = 255)
#    root_device_type = models.PositiveIntegerField(choices = rdtypes,
#                                                   verbose_name = 'Root Device Type')
#    location         = models.CharField(max_length = 255)
#    root_device_name = models.CharField(max_length = 255)
#    account          = models.ForeignKey(AwsAccount, null = True, blank = True)
#    owner_id         = models.CharField(max_length = 255)
#    platform         = models.CharField(max_length = 255)
#    architecture     = models.CharField(max_length = 255)
#    is_public        = models.BooleanField(default = False)
#    kernel_id        = models.CharField(max_length = 255)
#    region           = models.CharField(max_length = 64)
#    snapshot_id      = models.CharField(max_length = 64)
#    size             = models.FloatField(default = 0)
    
def updateAmi(all = False):
    rd = rdinv()
    added  = 0
    images = []
    for account in AwsAccount.objects.all():
        c = ec2(account)
        if all:
            amis = c.get_all_images()
        else:
            amis = c.get_all_images(owners = [account.account_number])
        for ami in amis:
            id = ami.id
            oid = ami.ownerId
            try:
                acc      = AwsAccount.objects.get(account_number = oid)
            except:
                acc = None
            if ami.region:
                region = ami.region.name or ''
            else:
                region = ''
            devtype  = rd.get(ami.root_device_type,0)
            arch     = ami.architecture
            if not arch:
                continue
            bd       = ami.block_device_mapping
            snapshot_id = ''
            size     = 0
            if bd:
                try:
                    rdn = ami.root_device_name
                    dev = bd.get(ami.root_device_name,None)
                    if dev:
                        size = dev.size
                        snapshot_id = dev.snapshot_id
                except:
                    pass
            image, created = AMI.objects.get_or_create(id = ami.id,
                                                       root_device_type = devtype)
            image.account = acc
            image.owner_id = oid
            image.name = ami.name or ''
            image.description = ami.description or ''
            image.region = region
            image.location = ami.location
            image.architecture = arch
            image.platform = ami.platform or ''
            image.root_device_name = ami.root_device_name or ''
            image.is_public = ami.is_public
            image.kernel_id = ami.kernel_id or ''
            image.snapshot_id = snapshot_id
            image.size = size
            image.save()
            images.append(image.id)
            if created:
                added += 1
        
        if all:
            break
        
    # Remove images not in images list
    re = AMI.objects.exclude(pk__in=images)
    removed = re.count()
    re.delete()
    return added,removed

