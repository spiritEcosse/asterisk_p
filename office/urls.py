from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'office'
urlpatterns = [
    path('', login_required(views.UserPositionCreate.as_view()), name='create'),
    path('list/', login_required(views.UserOfficeList.as_view()), name='list'),
    path('schedule/', login_required(views.ScheduleCreate.as_view()), name='schedule'),
    path('schedule_update/<int:pk>/', login_required(views.ScheduleUpdate.as_view()), name='schedule_update'),
    path('disconnect_users/', views.DisconnectUsers.as_view(), name='disconnect_users'),
]
