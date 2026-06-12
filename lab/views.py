import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import openpyxl
from openpyxl.styles import Font, Alignment

from config import settings
from .forms import UserRegisterForm, ApplianceForm, LocationForm
from django.utils.translation import get_language
from .models import Appliance, Location


def landing_page(request):
    return render(request, 'lab/landing.html')


def format_money(amount):
    return f"{int(amount):,}".replace(",", " ")


def format_kwh(amount):
    return f"{amount:.1f}"


def calculate_monthly_cost(kwh):
    if kwh <= 0:
        return 0

    cost = 0
    if kwh <= 200:
        cost = kwh * 650
    elif kwh <= 500:
        cost = (200 * 650) + ((kwh - 200) * 900)
    elif kwh <= 1000:
        cost = (200 * 650) + (300 * 900) + ((kwh - 500) * 1100)
    elif kwh <= 5000:
        cost = (200 * 650) + (300 * 900) + (500 * 1100) + ((kwh - 1000) * 1600)
    elif kwh <= 10000:
        cost = (200 * 650) + (300 * 900) + (500 * 1100) + (4000 * 1600) + ((kwh - 5000) * 1900)
    else:
        cost = (200 * 650) + (300 * 900) + (500 * 1100) + (4000 * 1600) + (5000 * 1900) + ((kwh - 10000) * 2200)

    return cost


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'lab/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'lab/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    locations = Location.objects.filter(user=request.user)
    appliances = Appliance.objects.filter(user=request.user).order_by('-id')

    if request.method == 'POST':
        if 'add_location' in request.POST:
            location_form = LocationForm(request.POST)
            if location_form.is_valid():
                new_loc = location_form.save(commit=False)
                new_loc.user = request.user
                new_loc.save()
                return redirect('dashboard')

        elif 'add_appliance' in request.POST:
            appliance_form = ApplianceForm(request.POST, user=request.user)
            if appliance_form.is_valid():
                new_app = appliance_form.save(commit=False)
                new_app.user = request.user

                new_app.monthly_kwh = (new_app.power_watts * new_app.hours_per_day / 1000) * new_app.quantity * 30
                new_app.co2_footprint = new_app.monthly_kwh * 0.5

                current_lang = get_language()

                if current_lang == 'ru':
                    prompt = f"В моем объекте '{new_app.location.name}' устройство '{new_app.appliance_name}' мощностью {new_app.power_watts} Вт работает {new_app.hours_per_day} часов в день. Дай 1 краткий совет по энергосбережению на русском языке."
                elif current_lang == 'en':
                    prompt = f"In my location '{new_app.location.name}', the appliance '{new_app.appliance_name}' ({new_app.power_watts} watts) runs for {new_app.hours_per_day} hours a day. Provide 1 short energy-saving tip in English."
                else:
                    prompt = f"Mening '{new_app.location.name}' obyektimda {new_app.power_watts} vattli {new_app.appliance_name} kuniga {new_app.hours_per_day} soat ishlaydi. Energiya tejash bo'yicha 1 ta qisqa maslahatni o'zbek tilida ber."

                # ===================================================
                #  YANGI "AQ" KALITLARNI ALDAB O'TISH USULI
                # ===================================================
                try:
                    from google import genai

                    # Kalitni settings.py dan olamiz!
                    api_key = settings.GEMINI_API_KEY
                    client = genai.Client(api_key=api_key)

                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=prompt,
                    )

                    new_app.auto_tip = response.text

                except Exception as e:
                    kalit_boshi = str(settings.GEMINI_API_KEY)[:15]
                    new_app.auto_tip = f"Serverdagi kalit: {kalit_boshi}... Xato: {str(e)[:300]}"
                # ===================================================

                new_app.save()
                return redirect('dashboard')

    location_form = LocationForm()
    appliance_form = ApplianceForm(user=request.user)

    total_monthly_kwh = appliances.aggregate(Sum('monthly_kwh'))['monthly_kwh__sum'] or 0
    total_co2 = appliances.aggregate(Sum('co2_footprint'))['co2_footprint__sum'] or 0
    monthly_cost = calculate_monthly_cost(total_monthly_kwh)

    projections = {
        'm1': {'kwh': format_kwh(total_monthly_kwh), 'cost': format_money(monthly_cost), 'co2': format_kwh(total_co2)},
        'm3': {'kwh': format_kwh(total_monthly_kwh * 3), 'cost': format_money(monthly_cost * 3),
               'co2': format_kwh(total_co2 * 3)},
        'm6': {'kwh': format_kwh(total_monthly_kwh * 6), 'cost': format_money(monthly_cost * 6),
               'co2': format_kwh(total_co2 * 6)},
        'y1': {'kwh': format_kwh(total_monthly_kwh * 12), 'cost': format_money(monthly_cost * 12),
               'co2': format_kwh(total_co2 * 12)},
    }

    chart_labels = [r.appliance_name for r in appliances]
    chart_kwh = [r.monthly_kwh for r in appliances]
    chart_co2 = [r.co2_footprint for r in appliances]

    context = {
        'locations': locations,
        'appliances': appliances,
        'location_form': location_form,
        'appliance_form': appliance_form,
        'total_monthly_kwh': round(total_monthly_kwh, 2),
        'total_co2': round(total_co2, 2),
        'projections': projections,
        'chart_labels': json.dumps(chart_labels),
        'chart_kwh': json.dumps(chart_kwh),
        'chart_co2': json.dumps(chart_co2),
    }
    return render(request, 'lab/dashboard.html', context)


@login_required(login_url='login')
def delete_record(request, pk):
    record = get_object_or_404(Appliance, pk=pk, user=request.user)
    record.delete()
    return redirect('dashboard')


@login_required
def export_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Elektr Sarfi va Prognoz"

    headers = [
        "Obyekt (Uy/Korxona)",
        "Jihoz nomi",
        "Soni",
        "Quvvati (Vt)",
        "Kunlik ish vaqti (soat)",
        "Kunlik sarf (kVt*s)",
        "1 Oylik sarf (kVt*s)",
        "3 Oylik sarf (kVt*s)",
        "6 Oylik sarf (kVt*s)",
        "1 Yillik sarf (kVt*s)",
        "CO2 Izi (kg)",
        "Tizim maslahati (AI)"
    ]
    ws.append(headers)

    for col_num, cell in enumerate(ws[1], 1):
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    records = Appliance.objects.filter(user=request.user)

    for record in records:
        daily = (record.power_watts * record.hours_per_day) / 1000 * record.quantity
        monthly = record.monthly_kwh or 0

        month_3 = round(monthly * 3, 2)
        month_6 = round(monthly * 6, 2)
        yearly = round(monthly * 12, 2)

        location_name = record.location.name if record.location else "Noma'lum"

        row = [
            location_name,
            record.appliance_name,
            record.quantity,
            record.power_watts,
            record.hours_per_day,
            round(daily, 2),
            monthly,
            month_3,
            month_6,
            yearly,
            record.co2_footprint,
            record.auto_tip
        ]
        ws.append(row)

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column].width = max_length + 2

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Elektr_sarfi_hisoboti.xlsx"'
    wb.save(response)

    return response


@login_required(login_url='login')
def guide_view(request):
    return render(request, 'lab/guide.html')
