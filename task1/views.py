from rest_framework.views import APIView
from rest_framework.response import Response


class TestView(APIView):
    
    def get(self, request, format=None):
        return Response({'msg': 'Hello There, it 100 box'})