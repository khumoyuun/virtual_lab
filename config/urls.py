from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # Tilni almashtiruvchi maxsus yo'nalish
    path('i18n/', include('django.conf.urls.i18n')),
]

# Barcha asosiy sahifalarimiz til prefiksi bilan ishlashi uchun
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('lab.urls')),
)