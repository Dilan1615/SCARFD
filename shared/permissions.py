from rest_framework import permissions


class IsAdminForMutation(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['create', 'update', 'partial_update', 'destroy']:
            return request.user.is_authenticated and request.user.rol == 'ADMIN'
        return request.user.is_authenticated
