from django import forms
from django.utils.translation import ugettext_lazy as _

from amazoncloud.models import Instance, AMI, IpAddress, Installer

class InstanceForm(forms.ModelForm):    
    class Meta:
        model = Instance
        

class InstallPackagesForm(forms.Form):
    
    packages = forms.ModelMultipleChoiceField(queryset = Installer.objects.all())
    
    def __init__(self, *args, **kwargs):
        platform = kwargs.pop('platform',None)
        super(InstallPackagesForm,self).__init__(*args, **kwargs)
        

class CreateImage(forms.ModelForm):
    instance = forms.CharField(widget = forms.HiddenInput(), required = False)
    
    class Meta:
        model = AMI
        fields = ['name','description','platform']
        
class CreateAddress(forms.ModelForm):
    '''
    Form used to create a new IP address
    '''
    class Meta:
        model = IpAddress
        fields = ['account']
        