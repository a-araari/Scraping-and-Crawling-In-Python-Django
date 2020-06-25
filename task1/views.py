from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import tbl_page_data


class PageDataGetView(APIView):
    # url={my url}&waiting={waiting time after page load}&scroll={scrollin page}&validation_key={our-secret-key}Return:1
    def get(self, request, format=None):
        """
        Create a row in tbl_page_data using the values in request.GET
        """
        url = waiting = scroll = secret_key = tbl = None
        try:
            secret_key = request.GET['validation_key']
            if not Token.objects.filter(key=secret_key).exists():
                raise Exception('Unvalid validation key!')

            url = request.GET['url']
            waiting = request.GET['waiting']
            scroll = request.GET['scroll']

            tbl = tbl_page_data(url=url, waiting=waiting, scroll=scroll)
            tbl.save()
            return Response({
                    'secret_key': secret_key,
                    'url': url,
                    'waiting': waiting,
                    'tbl_task_id': tbl.task_id,
                })
        except Exception as e:
            return Response({'err': e})
        else:
            pass
        finally:
            pass
        return Response({

            })


class PageDataSetView(APIView):

    def get(self, request, format=None):
        return Response({'ppp': request.GET.get('ppp')})
