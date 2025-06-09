from rest_framework.viewsets import ModelViewSet
from rest_framework import generics
from .models import User
from .serializers import (
    UserListSerializer,
    UserAddSerializer,
    UserAddResponseSerializer)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserListSerializer


