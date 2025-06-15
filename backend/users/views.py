import os
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken as drf_ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, mixins

from .models import User, Subscription
from .serializers import (
    UserViewSerializer,
    UserAddSerializer,
    UserWithRecipesSerializer,
    PasswordChangeSerializer,
    GetTokenSerializer,
    AvatarUploadSerializer,
    AvatarViewSerializer,
)


class UsersViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserViewSerializer
    permission_classes = [AllowAny]
    filterset_fields = []

    def get_serializer_class(self):
        if self.action == 'create':
            return UserAddSerializer
        return UserViewSerializer

    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated],
            url_path='set_password', url_name='set-password')
    def set_password(self, request, *args, **kwargs):
        """Изменить пароль текущего пользователя"""
        user = request.user

        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid() and user.check_password(
                serializer.validated_data['current_password']):
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated],
            url_path='me', url_name='me')
    def me(self, request):
        """Текущий пользователь"""
        instance = request.user
        serializer = self.get_serializer(instance=instance)
        return Response(serializer.data)

    @action(detail=False, methods=['PUT', 'DELETE'],
            permission_classes=[IsAuthenticated],
            url_path='me/avatar', url_name='me-avatar')
    def me_upload_or_delete_avatar(self, request):
        """Загрузка или удаление аватара текущего пользователя"""
        print('METHOD:', request.method)
        if request.method == 'DELETE':
            return self._delete_my_avatar(request)
        elif request.method == 'PUT':
            return self._upload_my_avatar(request)
        else:
            return Response({'detail': 'Метод не поддерживается'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _upload_my_avatar(self, request):
        user = request.user
        serializer = AvatarUploadSerializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        resp_serializer = AvatarViewSerializer(instance=user,
                                               context=self.get_serializer_context())
        return Response(resp_serializer.data,
                        status=status.HTTP_200_OK)

    def _delete_my_avatar(self, request):
        user = request.user
        if user.avatar:
            os.remove(user.avatar.path)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated],
            url_path='subscriptions', url_name='subscriptions')
    def subscriptions(self, request):
        """Мои подписки"""
        user = request.user
        queryset = user.subscriptions_my.all().prefetch_related('recipes')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserWithRecipesSerializer(page, many=True,
                                                   context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        else:
            serializer = UserWithRecipesSerializer(queryset, many=True,
                                                   context=self.get_serializer_context())
            return Response(serializer.data)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated],
            url_path='subscribe', url_name='subscribe-unsubscribe')
    def subscribe_unsubscribe(self, request, pk=None):
        """Подписаться или отписаться на пользователя"""
        user = request.user
        author = self.get_object()
        if user == author:
            return Response({'detail': 'Нельзя подписаться на себя'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            return self._subscribe(user, author)
        elif request.method == 'DELETE':
            return self._unsubscribe(user, author)
        else:
            return Response({'detail': 'Метод не поддерживается'},
                                               status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _subscribe(self, user, author):
        if Subscription.objects.filter(author=author, follower=user).count() > 0:
            return Response({'detail': 'Вы уже подписаны на данного пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)
        Subscription.objects.create(author=author, follower=user)
        serializer = UserWithRecipesSerializer(instance=author,
                                               context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _unsubscribe(self, user, author):
        """Отписаться от пользователя"""
        try:
            subscr = Subscription.objects.get(author=author, follower=user)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Вы не подписаны на данного пользователя'},
                            status=status.HTTP_404_NOT_FOUND)
        subscr.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ObtainAuthToken(drf_ObtainAuthToken):
    """Получение токена авторизации"""
    serializer_class = GetTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(self.serializer_class(instance=token).data)


class RemoveAuthToken(APIView):
    """Удаление токена авторизации текущего пользователя"""
    def post(self, request, *args, **kwargs):
        user = request.user
        if not (user and user.is_authenticated and user.auth_token):
            return Response({
                    'detail': 'Учетные данные не были предоставлены.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


obtain_auth_token = ObtainAuthToken.as_view()
remove_auth_token = RemoveAuthToken.as_view()
