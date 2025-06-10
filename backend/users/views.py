from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import User
from .serializers import (
    UserListSerializer,
    UserAddSerializer,
    PasswordChangeSerializer,
    GetTokenSerializer,
)


def get_current_user_tmp(request):
    return User.objects.first()


class UsersViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserListSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserAddSerializer
        # А если запрошенное действие — не 'list', применяем CatSerializer
        return UserListSerializer

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        #FIXME - переделать, когда разберусь с авторизацией
        user = get_current_user_tmp(request)

        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)



from rest_framework.authtoken.views import ObtainAuthToken as drf_ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


class ObtainAuthToken(drf_ObtainAuthToken):
    serializer_class = GetTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'auth_token': token.key,
        })

obtain_auth_token = ObtainAuthToken.as_view()


class RemoveAuthToken(APIView):
    def post(self, request, *args, **kwargs):
        #FIXME - переделать, когда разберусь с авторизацией
        user = get_current_user_tmp(request)
        if not user:
            return Response({
                    'detail': 'Учетные данные не были предоставлены.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        Token.objects.delete(pk=user.auth_token.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

remove_auth_token = RemoveAuthToken.as_view()
