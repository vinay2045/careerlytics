from django.urls import path
from . import views

app_name = 'jamai'

# Jamai App Configuration

urlpatterns = [
    path('jam/', views.jamai_page, name='jamai_page'),
    path('save/', views.save_recording, name='save_recording'),
    path('delete/<int:recording_id>/', views.delete_recording, name='delete_recording'),
    path('get-recordings/', views.get_recordings, name='get_recordings'),
]
