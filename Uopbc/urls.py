from django.urls import path
from . import views
urlpatterns = [
    path('', views.index,name='indexSearch'),
    path('result',views.result,name='finalResult'),
    path('pieresult',views.pieResult,name='piefinalResult')
]
