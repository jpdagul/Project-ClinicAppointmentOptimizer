"""
URL routing for API endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('upload', views.upload_csv, name='upload_csv'),
    path('predictions', views.get_predictions, name='get_predictions'),
    path('clear', views.clear_data, name='clear_data'),
    path('dashboard/metrics', views.get_dashboard_metrics, name='get_dashboard_metrics'),
    path('dashboard/weekly-performance', views.get_weekly_performance, name='get_weekly_performance'),
    path('dashboard/overbooking-strategies', views.get_overbooking_strategies, name='get_overbooking_strategies'),
    path('dashboard/insights', views.get_dashboard_insights, name='get_dashboard_insights'),
    path('simulation/run', views.run_simulation, name='run_simulation'),
]

