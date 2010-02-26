from dateutil.parser import parse as parseDate
from amazoncloud.models import AwsAccount, AMI, SecurityGroup, KeyPair, Instance, rddict, ec2


def rdinv():
    d = {}
    for k,v in rddict.items():
        d[v] = k
    return d


class AWS(object):
    
    def __init__(self):
        self.rd = rdinv()
        
    def sync_accounts(self):
        for account in AwsAccount.objects.all():
            c = self.__updategroups(account)
        
    def update(self, ami, acc = None):
        if ami.region:
            region = ami.region.name or ''
        else:
            region = ''
        devtype  = self.rd.get(ami.root_device_type,0)
        arch     = ami.architecture
        if not arch:
            None,False
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
        image.owner_id = ami.ownerId
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
        return image, created
    
    def __updategroups(self, account):
        c = ec2(account)
        groups = c.get_all_security_groups()
        gs = []
        for group in groups:
            g,created = SecurityGroup.objects.get_or_create(name = group.name,
                                                            account = account)
                                                    #region = group.region.name)
            gs.append(g.id)
        SecurityGroup.objects.exclude(pk__in=gs).delete()
        #
        #update key-value pairs
        groups = c.get_all_key_pairs()
        gs = []
        for group in groups:
            g,created = KeyPair.objects.get_or_create(name = group.name,
                                                      fingerprint = group.fingerprint,
                                                      material = group.material or '',
                                                      account = account)
            gs.append(g.id)
        KeyPair.objects.exclude(pk__in=gs).delete()
        return c
        
    def __call__(self, all = True):
        c = None
        added  = 0
        images = []
        for account in AwsAccount.objects.all():
            c = self.__updategroups(account)
            amis = c.get_all_images(owners = [account.account_number])
            for ami in amis:
                image, created = self.update(ami,account)
                if image:
                    images.append(image.id)
                    if created:
                        added += 1
        if all and c:
            amis = c.get_all_images()
            for ami in amis:
                try:
                    AwsAccount.objects.get(account_number = ami.ownerId)
                    continue
                except:
                    image, created = self.update(ami)
                    if image:
                        images.append(image.id)
                        if created:
                            added += 1
                
        
        # Remove images not in images list
        re = AMI.objects.exclude(pk__in=images)
        removed = re.count()
        re.delete()
        return added,removed


def updateReservation(res):
    account = AwsAccount.objects.get(account_number = res.owner_id)
    reg     = res.region.name
    groups  = []
    instances = []
    for g in res.groups:
        groups.append(SecurityGroup.objects.get(name = g.id, account = account))
    for inst in res.instances:
        ami   = AMI.objects.get(id = inst.image_id)
        dt    = parseDate(inst.launch_time)
        key   = KeyPair.objects.get(name = inst.key_name, account = account)
        ain, created = Instance.objects.get_or_create(id = inst.id,
                                                      account = account,
                                                      ami = ami,
                                                      key_pair = key)
        ain.timestamp = dt
        ain.region = reg
        ain.state = inst.state
        ain.type  = inst.instance_type
        ain.private_dns_name = inst.private_dns_name
        ain.public_dns_name = inst.public_dns_name
        ain.ip_address = inst.ip_address or ''
        ain.monitored  = inst.monitored
        ain.security_groups.clear()
        for g in groups:
            ain.security_groups.add(g)
        ain.save()
        instances.append(ain.id)
    return instances


def updateInstances():
    instances = []
    for account in AwsAccount.objects.all():
        c = ec2(account)
        reservations = c.get_all_instances()
        for res in reservations:
            instances.extend(updateReservation(res))    
    re = Instance.objects.exclude(pk__in=instances)
    re.delete()        
