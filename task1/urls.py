from django.urls import path
from task1 import views


urlpatterns = [
    # GET: local path : /set/?url={my url}&waiting={waiting time}&scroll={scrollin page}&validation_key={our-secret-key}
    path('set/', views.PageDataSetView.as_view()),
    # SET: local path : /set/?task_id={task id}&validation_key={our-secret-key}
    path('get/', views.PageDataGetView.as_view()),
]