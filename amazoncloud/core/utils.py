from dateutil.parser import parse as parseDate
from amazoncloud.models import AwsAccount, AMI, Instance, rddict, ec2


def rdinv():
    d = {}
    for k,v in rddict.items():
        d[v] = k
    return d

    
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
            if acc:
                image.our = True
            else:
                image.our = False
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


def updateInstances():
    instances = []
    for account in AwsAccount.objects.all():
        c = ec2(account)
        reservations = c.get_all_instances()
        for res in reservations:
            for inst in res.instances:
                ami   = AMI.objects.get(id = inst.image_id)
                dt    = parseDate(inst.launch_time)
                ain, created = Instance.objects.get_or_create(id = inst.id,
                                                              ami = ami,
                                                              timestamp = dt)
                ain.state = inst.state
                ain.type  = inst.instance_type
                ain.private_dns_name = inst.private_dns_name
                ain.public_dns_name = inst.public_dns_name
                ain.ip_address = inst.ip_address or ''
                ain.monitored  = inst.monitored
                ain.save()
                instances.append(ain.id)
    
    re = Instance.objects.exclude(pk__in=instances)
    re.delete()
        
        
