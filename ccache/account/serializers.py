'''
Serializer classes for account app are defined here.
'''

from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.authtoken.models import Token


class UserSerializer(ModelSerializer):
    '''
    Serializer class for User class that adds a token field generated
    by restframework's authtoken module.
    '''
    token = SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['username', 'password', 'email', 'token']
        extra_kwargs = {'password':{'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        new_user = get_user_model()(
            username=validated_data.get("username"),
            email=validated_data.get("email", "")
            )
        new_user.set_password(password)
        new_user.save()
        return new_user

    def update(self, instance, validated_data):
        new_password = validated_data.get('password', False)
        instance.email = validated_data.get('email', instance.email)
        if new_password:
            instance.set_password(new_password)
        instance.save()
        return instance

    def save(self, **kwargs):
        user = super().save(**kwargs)
        if not Token.objects.filter(user=user).exists():
            Token.objects.create(user=user)
        return user

    def get_token(self, obj):
        '''
        In charge of generating value for SerializerMethodField token.
        '''
        try:
            return obj.auth_token.key
        except Token.DoesNotExist:
            return ''
