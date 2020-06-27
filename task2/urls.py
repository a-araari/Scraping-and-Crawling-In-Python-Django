from django.urls import path
from task2 import views


urlpatterns = [
    # GET: local path : /set/?url={my url}&waiting={waiting time}&limit={crawk limit}&scroll={scrollin page}&validation_key={our-secret-key}
    path('set/', views.CrawlSetView.as_view()),
    # SET: local path : /set/?task_id={task id}&validation_key={our-secret-key}
    path('get/', views.CrawlGetView.as_view()),
]