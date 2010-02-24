
from amazoncloud.models import AwsAccount, AMI, rddict


def rdinv():
    d = {}
    for k,v in rddict.items():
        d[v] = k
    return d


def updateAmi():
    rd = rdinv()
    for account in AwsAccount.objects.all():
        c = ec2(account)
        amis = c.get_all_images(owners = [account.account_number])
        for ami in amis:
            defaults = {'account': account,
                        'name': ami.name or '',
                        'architecture': ami.architecture or '',
                        'root_device_type': rd.get(ami.root_device_type,0),
                        'root_device_name': ami.root_device_name or '',
                        'is_public': ami.is_public}
            image, created = AMI.objects.get_or_create(id = ami.id, **defaults)
            