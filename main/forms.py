from django import forms
from .models import Member, Price

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['full_name', 'birthday', 'email', 'phone', 'start_date', 'end_date', 'remarks', 'nfc_tag_uid']

    def __init__(self, *args, **kwargs):
        super(MemberForm, self).__init__(*args, **kwargs)

        # Set required fields
        self.fields['full_name'].required = True
        self.fields['phone'].required = True
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False
        self.fields['nfc_tag_uid'].required = False

        # Set not required fields
        self.fields['birthday'].required = False
        self.fields['email'].required = False
        self.fields['remarks'].required = False

class PriceForm(forms.ModelForm):
    class Meta:
        model = Price
        fields = ['name', 'duration', 'price']
        
class ExtendMembershipForm(forms.Form):
    extension_duration = forms.ChoiceField(
        choices=[
            ('1', '1 Month'),
            ('3', '3 Months'),
            ('6', '6 Months'),
            ('12', '1 Year'),
        ],
        label="Extend by"
    )
