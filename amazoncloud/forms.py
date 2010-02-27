from django import forms
from django.utils.translation import ugettext_lazy as _

from amazoncloud.models import Instance

class InstanceForm(forms.ModelForm):    
    class Meta:
        model = Instance