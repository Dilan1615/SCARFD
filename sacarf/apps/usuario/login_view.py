from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

    email = request.data.get('email', '')
    UserModel = get_user_model()

    try:
        user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        return Response(
            {'detail': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if user.esta_bloqueado():
        tiempo_restante = user.bloqueado_hasta - timezone.now() if user.bloqueado_hasta else timedelta(minutes=30)
        minutos = int(tiempo_restante.total_seconds() // 60)
        return Response(
            {
                'detail': f'Cuenta bloqueada por múltiples intentos fallidos. Intenta de nuevo en {minutos} minuto(s).',
                'intentos_restantes': 0,
                'bloqueado': True,
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    serializer = TokenObtainPairSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
    except Exception:
        user.intentos_fallidos += 1
        user.save()

        intentos_restantes = max(0, 5 - user.intentos_fallidos)

        if user.intentos_fallidos >= 5:
            user.bloqueado_hasta = timezone.now() + timedelta(minutes=30)
            user.save()
            return Response(
                {
                    'detail': 'Cuenta bloqueada por múltiples intentos fallidos. Intenta de nuevo en 30 minutos.',
                    'intentos_restantes': 0,
                    'bloqueado': True,
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(
            {
                'detail': f'Credenciales inválidas. Te quedan {intentos_restantes} intento(s).',
                'intentos_restantes': intentos_restantes,
                'bloqueado': False,
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    user.save()
    return Response(serializer.validated_data, status=status.HTTP_200_OK)
