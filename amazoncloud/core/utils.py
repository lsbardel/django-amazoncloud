from dateutil.parser import parse as parseDate
from amazoncloud.models import AwsAccount, IpAddress, AMI, SecurityGroup, \
                               SnapShot, EbsVolume, KeyPair, Instance, rddict, ec2

SIZE_S3_AMI = 10

def rdinv():
    d = {}
    for k,v in rddict.items():
        d[v] = k
    return d


class AWS(object):
    '''
    AWS syncronizer
    '''
    def __init__(self):
        self.rd = rdinv()
        self.init()
    
    def init(self):
        self.snaps = []
        self.amis = []
        self.vols = []
        self.instances = []
        self.ips = []
        self.groups = []
        self.keys = []
        
    def sync_private(self):
        for account in AwsAccount.objects.all():
            # securitygroup and keypair
            c = self.__updategroups(account)
            # snapshots
            snaps = c.get_all_snapshots(owner = "self")
            for snap in snaps:
                self.__update_snap(snap,account)
            # ami
            amis = c.get_all_images(owners = [account.id])
            for ami in amis:
                self.__update_ami(ami,account)
            # volumes
            vols = c.get_all_volumes()
            for vol in vols:
                self.__update_vol(vol,account)
            # instances
            reservations = c.get_all_instances()
            for res in reservations:
                self.updateReservation(res)
            # elastic IPs
            allips = c.get_all_addresses()
            for ip in allips:
                g,created = IpAddress.objects.get_or_create(account = account,
                                                            ip = ip.public_ip)
                if ip.instance_id:
                    g.instance = Instance.objects.get(id = ip.instance_id)
                g.save()
                self.ips.append(g.id)
        self.clear()
        self.init()
    
    def get_snapshot(self, id):
        '''
        Get a snapshot from snapshot ID
        '''
        try:
            return SnapShot.objects.get(id = id)
        except:
            snaps = c.get_all_snapshots(snapshot_ids = [id])
            if snaps:
                return self.__update_snap(snaps[0])
    
    
    def __update_snap(self, snap, account = None):
        nsnap, created    = SnapShot.objects.get_or_create(id = snap.id,
                                                           size = snap.volume_size)
        nsnap.account     = account
        nsnap.owner_id    = snap.owner_id
        nsnap.description = nsnap.description or ''
        nsnap.state       = snap.status
        nsnap.timestamp   = parseDate(snap.start_time)
        if account:
            nsnap.our = True
        nsnap.save()
        self.snaps.append(nsnap.id)
        return nsnap
        
    def __update_ami(self, ami, acc = None):
        if ami.region:
            region = ami.region.name or ''
        else:
            region = ''
        devtype  = self.rd.get(ami.root_device_type,0)
        arch     = ami.architecture
        if not arch:
            None,False
        bd       = ami.block_device_mapping
        snapshot = None
        size     = 0
        if bd:
            try:
                rdn = ami.root_device_name
                dev = bd.get(ami.root_device_name,None)
                if dev:
                    size = dev.size
                    snapshot = self.get_snapshot(dev.snapshot_id)
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
        image.snapshot = snapshot
        image.ramdisk_id = ami.ramdisk_id or ''
        image.size = size
        if acc:
            image.our = True
        else:
            image.our = False
        image.save()
        return image, created
    
    def __update_vol(self, vol, account):
        v,created = EbsVolume.objects.get_or_create(id = vol.id,
                                                    account = account,
                                                    size = vol.size)
        if vol.snapshot_id:
            v.snapshot = self.get_snapshot(vol.snapshot_id)
        v.region    = vol.zone
        v.timestamp = parseDate(vol.create_time)
        v.state     = vol.status
        v.save()
        self.vols.append(v.id)
        return v
        
    
    def __updategroups(self, account):
        c = ec2(account)
        groups = c.get_all_security_groups()
        for group in groups:
            g,created = SecurityGroup.objects.get_or_create(name = group.name,
                                                            account = account)
                                                    #region = group.region.name)
            self.groups.append(g.id)
        #
        #update key-value pairs
        groups = c.get_all_key_pairs()
        for group in groups:
            g,created = KeyPair.objects.get_or_create(name = group.name,
                                                      fingerprint = group.fingerprint,
                                                      account = account)
            if group.material:
                g.material = group.material
            g.dump()
            self.keys.append(g.id)
        
        return c
        
    def __call__(self, all = True):
        c = None
        added  = 0
        images = []
        for account in AwsAccount.objects.all():
            c = self.__updategroups(account)
            amis = c.get_all_images(owners = [account.id])
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
                    AwsAccount.objects.get(id = ami.ownerId)
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


    def updateReservation(self, res):
        account = AwsAccount.objects.get(id = res.owner_id)
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
            ain.persistent = inst.persistent
            ain.region = reg
            ain.state = inst.state
            ain.type  = inst.instance_type
            ain.private_dns_name = inst.private_dns_name
            ain.public_dns_name = inst.public_dns_name
            ain.ip_address = inst.ip_address or ''
            ain.monitored  = inst.monitored
        
            try:
                ebsblock   = inst.block_device_mapping[inst.root_device_name]
                ain.volume = EbsVolume.objects.get(id = ebsblock.volume_id)
                ain.size   = ain.volume.size
            except:
                pass
        
            ain.security_groups.clear()
            for g in groups:
                ain.security_groups.add(g)
                ain.save()
            self.instances.append(ain.id)

    def clear(self, all = False):
        Instance.objects.exclude(pk__in = self.instances).delete()
        IpAddress.objects.exclude(pk__in = self.ips).delete()
        SecurityGroup.objects.exclude(pk__in=self.groups).delete()
        KeyPair.objects.exclude(pk__in=self.keys).delete()
        EbsVolume.objects.exclude(ph__in = self.vols).delete()
        if all:
            SnapShot.objects.exclude(pk__in = self.snaps).delete()
            AMI.objects.exclude(pk__in = self.amis).delete()
    