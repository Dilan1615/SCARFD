import re
from django.conf import settings
from rest_framework import serializers
from .models import Usuario

def validar_password_segura(value):
    errors = []
    if not re.search(r'[A-Z]', value):
        errors.append('Debe contener al menos una mayúscula')
    if not re.search(r'[0-9]', value):
        errors.append('Debe contener al menos un número')
    if not re.search(r'[^A-Za-z0-9]', value):
        errors.append('Debe contener al menos un símbolo especial')
    if errors:
        raise serializers.ValidationError('. '.join(errors))

class UsuarioSerializer(serializers.ModelSerializer):
    foto_referencia_url = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'first_name', 'last_name', 'cedula', 'telefono', 'rol', 'foto_referencia_url', 'is_active']
        read_only_fields = ['id', 'is_active']

    def get_foto_referencia_url(self, obj):
        val = obj.foto_referencia_url
        if not val:
            return None
        if val.startswith('http'):
            return val
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri('/' + settings.MEDIA_URL + val)
        return '/' + settings.MEDIA_URL + val

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    foto_referencia_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = [ 'email', 'password', 'first_name', 'last_name', 'cedula', 'telefono', 'rol', 'foto_referencia_url']

    def validate_password(self, value):
        validar_password_segura(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Usuario.objects.create_user(
            password=password,
            **validated_data
        )
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_new_password(self, value):
        validar_password_segura(value)
        return value

class SolicitarRestablecimientoSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not Usuario.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Este correo no está registrado")
        return value.lower() 

class RestablecerPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate_password(self, value):
        validar_password_segura(value)
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Las contraseñas no coinciden'})
        return data
