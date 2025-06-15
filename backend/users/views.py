import os
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken as drf_ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import User, Subscription
from .serializers import (
    UserViewSerializer,
    UserAddSerializer,
    UserWithRecipesSerializer,
    PasswordChangeSerializer,
    GetTokenSerializer,
    AvatarUploadSerializer,
)


class UsersViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserViewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = []

    def get_serializer_class(self):
        if self.action == 'create':
            return UserAddSerializer
        # А если запрошенное действие — не 'list', применяем CatSerializer
        return UserViewSerializer

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated],
            url_path='set_password', url_name='set-password')
    def set_password(self, request, *args, **kwargs):
        """Изменить пароль текущего пользователя"""
        user = request.user

        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='me', url_name='me')
    def me(self, request):
        """Текущий пользователь"""
        instance = request.user
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['put'],
            permission_classes=[IsAuthenticated],
            url_path='me/avatar', url_name='me')
    def me_upload_avatar(self, request):
        """Загрузка аватара текущего пользователя"""
        user = request.user

        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'],
            permission_classes=[IsAuthenticated],
            url_path='me/avatar', url_name='me')
    def me_delete_avatar(self, request):
        """Удаление аватара текущего пользователя"""
        user = request.user
        if user.avatar:
            os.remove(user.avatar.path)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='subscriptions', url_name='subscriptions')
    def subscriptions(self, request):
        """Мои подписки"""
        user = request.user
        user.subscriptions_my.all()

        queryset = user.subscriptions_my.all().prefetch_related('recipes')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserWithRecipesSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = UserWithRecipesSerializer(page, many=True)
            return Response(serializer.data)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated],
            url_path='subscribe', url_name='subscribe')
    def subscribe(self, request, pk=None):
        """Подписаться на пользователя"""
        user = request.user
        author = self.get_object()
        Subscription.objects.get_or_create(author=author, follower=user)
        serializer = UserWithRecipesSerializer(instance=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'],
            permission_classes=[IsAuthenticated],
            url_path='subscribe', url_name='unsubscribe')
    def unsubscribe(self, request, pk=None):
        """Отписаться от пользователя"""
        user = request.user
        author = self.get_object()

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
        return Response({
            'auth_token': token.key,
        })


class RemoveAuthToken(APIView):
    """Удаление токена авторизации текущего пользователя"""
    def post(self, request, *args, **kwargs):
        user = request.user
        if not user:
            return Response({
                    'detail': 'Учетные данные не были предоставлены.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        Token.objects.delete(pk=user.auth_token.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


obtain_auth_token = ObtainAuthToken.as_view()
remove_auth_token = RemoveAuthToken.as_view()
