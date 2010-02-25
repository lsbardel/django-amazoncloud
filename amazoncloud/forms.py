from django import forms

from amazoncloud.models import Instance

class InstanceForm(forms.ModelForm):
    
    class Meta:
        model = Instance