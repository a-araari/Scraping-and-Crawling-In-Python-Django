from django.urls import path
from task2 import views


urlpatterns = [
    # api_main_url/crawl/set/?url={my url}&limit={url-crawl-limitation}&waiting={waiting time after pageload}&scroll={scroll in page}&validation_key={our-secret-key}
    path('set/', views.CrawlSetView.as_view()),
    path('get/', views.CrawlGetView.as_view()),
]