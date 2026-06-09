import google.generativeai as genai
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
import google.generativeai as genai


class Appliance(models.Model):
    name = models.CharField(max_length=100, verbose_name="Qurilma nomi")
    avg_power_watts = models.FloatField(verbose_name="O'rtacha quvvati (Vatt)")
    category = models.CharField(max_length=50, verbose_name="Kategoriya")

    def __str__(self):
        return self.name


# 1. Yangi: Uy yoki Korxona uchun model


class Location(models.Model):
    LOCATION_TYPES = (
        ('home', ('Uy')),  # _() qavsga olindi
        ('business', ('Korxona')),  # _() qavsga olindi
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text=("Masalan: Asosiy uy, Do'kon, Sex"))  # _() qavsga olindi
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, default='home')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"


class Appliance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)
    appliance_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    power_watts = models.FloatField()
    hours_per_day = models.FloatField()
    monthly_kwh = models.FloatField(null=True, blank=True)
    co2_footprint = models.FloatField(null=True, blank=True)
    auto_tip = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.appliance_name


class ConsumptionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')
    appliance_name = models.CharField(max_length=100, verbose_name="Qurilma nomi")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Soni")
    power_watts = models.FloatField(verbose_name="Quvvati (Vatt)")
    hours_per_day = models.FloatField(verbose_name="Kunlik ishlash vaqti (soat)")

    daily_kwh = models.FloatField(verbose_name="Kunlik sarf (kVt*s)", blank=True, null=True)
    monthly_kwh = models.FloatField(verbose_name="Oylik sarf (kVt*s)", blank=True, null=True)
    co2_footprint = models.FloatField(verbose_name="CO2 izi (kg)", blank=True, null=True)
    auto_tip = models.TextField(verbose_name="Avtomatik maslahat", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 1. Matematik hisob-kitoblar
        total_power = self.power_watts * self.quantity
        self.daily_kwh = round((total_power * self.hours_per_day) / 1000, 2)
        self.monthly_kwh = round(self.daily_kwh * 30, 2)
        self.co2_footprint = round(self.monthly_kwh * 0.5, 2)

        # 2. Sun'iy intellekt yordamida unikal maslahat olish (Avto-aniqlash tizimi)
        try:
            import google.generativeai as genai
            from django.conf import settings

            # API'ni sozlash
            genai.configure(api_key=settings.GEMINI_API_KEY)

            # Kalitimiz uchun ruxsat berilgan barcha modellarni qidiramiz
            valid_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    valid_models.append(m.name)

            # Mavjudlaridan eng yaxshisini avtomatik tanlaymiz
            chosen_model_name = None
            for preferred in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro',
                              'models/gemini-1.0-pro']:
                if preferred in valid_models:
                    chosen_model_name = preferred.replace('models/', '')
                    break

            # Agar yuqoridagilar topilmasa, ro'yxatdagi borini olamiz
            if not chosen_model_name and valid_models:
                chosen_model_name = valid_models[0].replace('models/', '')

            # Agar mos model topilgan bo'lsa, so'rov jo'natamiz
            if chosen_model_name:
                model = genai.GenerativeModel(chosen_model_name)
                prompt = f"O'zbek tilida qisqa va aniq javob ber. Men elektr energiyasi sarfini hisoblaydigan dastur qilyapman. Foydalanuvchi tizimga {self.quantity} ta '{self.appliance_name}' kiritdi. 1 donasining quvvati {self.power_watts} Vatt. Ular kuniga {self.hours_per_day} soat ishlaydi. Ushbu jihoz(lar)ni ishlatishda elektr energiyasini va atrof-muhitni asrash bo'yicha qanday real tejamkorlik qilsa bo'ladi? Atigi 1 yoki 2 ta juda amaliy maslahat yoz. Ortiqcha so'zlar va salomlashishlarsiz, to'g'ridan-to'g'ri maslahatni o'zini yoz."

                response = model.generate_content(prompt)
                self.auto_tip = f"🤖 AI Maslahati: {response.text.strip()}"
            else:
                self.auto_tip = f"Sun'iy intellektga ulanishda xato: Kalit uchun mos model topilmadi. Mavjud modellar: {valid_models}"

        except Exception as e:
            self.auto_tip = f"Sun'iy intellektga ulanishda xato: {str(e)}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.appliance_name} ({self.quantity} ta)"
