from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _  # Tarjima funksiyasi qo'shildi
from .models import Appliance, Location


# 1. Ro'yxatdan o'tish (Register) formasi
class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text=_('Ixtiyoriy'))

    class Meta:
        model = User
        fields = ['username', 'first_name']


# 2. Obyekt (Uy/Korxona) qo'shish formasi
class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'location_type']
        labels = {
            'name': _('Obyekt nomi'),
            'location_type': _('Turi'),
        }
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _("Masalan: Asosiy uy, Yozgi hovli, Do'kon...")}),
            'location_type': forms.Select(attrs={'class': 'form-select'}),
        }


# 3. Jihoz qo'shish formasi
class ApplianceForm(forms.ModelForm):
    class Meta:
        model = Appliance
        fields = ['location', 'appliance_name', 'quantity', 'power_watts', 'hours_per_day']
        labels = {
            'location': _("Qaysi obyektga qo'shilmoqda?"),
            'appliance_name': _("Jihoz nomi"),
            'quantity': _("Soni"),
            'power_watts': _("Quvvati (Vatt)"),
            'hours_per_day': _("Kunlik ishlash vaqti (Soat)"),
        }
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select'}),
            'appliance_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _('Masalan: Muzlatgich...')}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'power_watts': forms.NumberInput(attrs={'class': 'form-control'}),
            'hours_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    # Jihoz qo'shayotganda ro'yxatda faqat shu foydalanuvchining o'z uylari chiqishi uchun
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ApplianceForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['location'].queryset = Location.objects.filter(user=user)

    # 24 soatlik cheklov
    def clean_hours_per_day(self):
        hours = self.cleaned_data.get('hours_per_day')
        if hours is not None:
            if hours > 24:
                raise forms.ValidationError(_("Xato: Bir kunda 24 soatdan ko'p vaqt bo'lishi mumkin emas!"))
            if hours < 0:
                raise forms.ValidationError(_("Xato: Vaqt manfiy raqam bo'lishi mumkin emas!"))
        return hours
