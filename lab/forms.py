from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import ConsumptionRecord

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Elektron pochta")
    first_name = forms.CharField(required=True, label="Ism")
    last_name = forms.CharField(required=True, label="Familiya")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']



class ConsumptionRecordForm(forms.ModelForm):
    class Meta:
        model = ConsumptionRecord
        fields = ['appliance_name', 'quantity', 'power_watts', 'hours_per_day']
        labels = {
            'appliance_name': "Qurilma nomi (masalan, Lampochka)",
            'quantity': "Soni (nechta, masalan: 20)",
            'power_watts': "Bitta qurilma quvvati (Vatt)",
            'hours_per_day': "Kunlik ishlash vaqti (soat)"
        }