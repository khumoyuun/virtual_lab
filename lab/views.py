import json
import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .forms import UserRegisterForm, ConsumptionRecordForm
from .models import ConsumptionRecord


# --- Sonlarni chiroyli formatlash uchun yordamchi funksiyalar ---
def format_money(amount):
    return f"{int(amount):,}".replace(",", " ")


def format_kwh(amount):
    return f"{amount:.1f}"


# --- YANGI: Differensial tarif hisoblash funksiyasi (2026-yil 1-iyundan keyin) ---
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


# ----------------------------------------------------------------

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
    records = request.user.records.all().order_by('-created_at')

    total_monthly_kwh = records.aggregate(Sum('monthly_kwh'))['monthly_kwh__sum'] or 0
    total_co2 = records.aggregate(Sum('co2_footprint'))['co2_footprint__sum'] or 0

    # --- XARAJATLAR VA VAQT PROGNOZI (Differensial tarif asosida) ---
    monthly_cost = calculate_monthly_cost(total_monthly_kwh)

    projections = {
        'm1': {
            'kwh': format_kwh(total_monthly_kwh),
            'cost': format_money(monthly_cost),
            'co2': format_kwh(total_co2)
        },
        'm3': {
            'kwh': format_kwh(total_monthly_kwh * 3),
            'cost': format_money(monthly_cost * 3),
            'co2': format_kwh(total_co2 * 3)
        },
        'm6': {
            'kwh': format_kwh(total_monthly_kwh * 6),
            'cost': format_money(monthly_cost * 6),
            'co2': format_kwh(total_co2 * 6)
        },
        'y1': {
            'kwh': format_kwh(total_monthly_kwh * 12),
            'cost': format_money(monthly_cost * 12),
            'co2': format_kwh(total_co2 * 12)
        },
    }

    chart_labels = [r.appliance_name for r in records]
    chart_kwh = [r.monthly_kwh for r in records]
    chart_co2 = [r.co2_footprint for r in records]

    if request.method == 'POST':
        form = ConsumptionRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            return redirect('dashboard')
    else:
        form = ConsumptionRecordForm()

    context = {
        'form': form,
        'records': records,
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
    record = get_object_or_404(ConsumptionRecord, pk=pk, user=request.user)
    record.delete()
    return redirect('dashboard')


@login_required(login_url='login')
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lab_results.csv"'

    writer = csv.writer(response)
    writer.writerow(['Jihoz nomi', 'Soni', 'Quvvati (Vt)', 'Kunlik vaqt (soat)', 'Oylik sarf (kVt*s)', 'CO2 Izi (kg)',
                     'Tizim maslahati'])

    records = request.user.records.all().order_by('-created_at')
    for r in records:
        writer.writerow(
            [r.appliance_name, r.quantity, r.power_watts, r.hours_per_day, r.monthly_kwh, r.co2_footprint, r.auto_tip])

    return response


@login_required(login_url='login')
def guide_view(request):
    return render(request, 'lab/guide.html')