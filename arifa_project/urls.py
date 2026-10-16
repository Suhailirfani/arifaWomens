from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home_view
from accounts.views import redirect_dashboard, login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('redirect-dashboard/', redirect_dashboard, name='redirect_dashboard'),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('students/', include('students.urls')),
    path('staff/', include('staff.urls')),
    path('attendance/', include('attendance.urls')),
    path('fees/', include('fees.urls')),
    path('examinations/', include('examinations.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
