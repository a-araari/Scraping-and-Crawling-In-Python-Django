from django.urls import path
from task1 import views


urlpatterns = [
    # api_main_url/page_data/set/?url={my url}&waiting={waiting time after page load}&scroll={scrollin page}&validation_key={our-secret-key}
    path('api_main_url/page_data/set/', views.TestView.as_view())
]