from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import tbl_crawl_task
from .options import start_crawl_task

def check_key_validation(key):
    """
    check secret key validation in the database
    raise exception if key is unvalid
    """
    if not Token.objects.filter(key=key).exists():
        raise Exception('Unvalid validation key!')


class CrawlSetView(APIView):
    # Args: ?url & limit & waiting & scroll & validation_key
    def get(self, request, format=None):
        """
        Create a row in tbl_crawl_task using the values in request.GET
        """
        try:
            secret_key = request.GET['validation_key']
            check_key_validation(secret_key)

            url = request.GET['url']
            waiting = request.GET['waiting']
            scroll = request.GET['scroll']
            limit = request.GET.get('limit', None)

            tbl = tbl_crawl_task(url=url, limit=limit, waiting=waiting, scroll=scroll)
            tbl.save()

            # starting the crawl task in a seperate Thread
            start_crawl_task(tbl)

            return Response({
                    'data': {
                        'task_id': tbl.task_id,
                        'url': tbl.url,
                        'pending_task': tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PENDING_STATUS).count(),
                    }
                })
        except Exception as e:
            return Response({
                    'data': {
                        'error': str(e),
                    }
                })


class CrawlGetView(APIView):
    # Args: ?url & validation_key
    def get(self, request, format=None):
        """
        Create a row in tbl_crawl_task using the values in request.GET
        """
        pass