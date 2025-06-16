from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrCreateAndReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.method == 'POST':
            return request.user and request.user.is_authenticated

        if request.method in ('DELETE', 'PATCH', 'PUT'):
            return (request.user
                    and request.user.is_authenticated
                    and obj.author == request.user)
        return False


class IsUserSelfOrCreateAndReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'POST' or request.method in SAFE_METHODS:
            return True

        if request.method in ('DELETE', 'PATCH', 'PUT'):
            return obj == request.user

        return False
