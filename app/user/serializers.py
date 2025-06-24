from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile
from django.core.mail import send_mail
import random
from django.conf import settings

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.save()
        # Create a UserProfile instance for the new user
        UserProfile.objects.create(user=user, display_name=validated_data['username'], email=validated_data['email'])
        return user
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Invalid credentials")
        
        refresh = RefreshToken.for_user(user)
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }
        return response_data
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        otp = str(random.randint(100000, 999999))
        self.context['request'].session['password_reset_otp'] = otp
        self.context['request'].session['otp_email'] = value

        send_mail(
            subject="Your Password Reset OTP",
            message=(
                f"Hi there,\n\n"
                f"We received a request to reset the password for your account.\n"
                f"To proceed, please use the following One-Time Password (OTP):\n\n"
                f"{otp}\n\n"
                f"This OTP is valid for the next 10 minutes.\n"
                f"If you did not request this, please ignore this email or contact support.\n\n"
                f"Thanks,\n"
                f"The Support Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[value],
            fail_silently=False,
        )

        # Store OTP for later use in save()
        self._otp = otp
        return value

    def save(self, request):
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{request.build_absolute_uri('/api/password-reset-confirm/')}{uid}/{token}/"

        return {"reset_link": reset_link, "otp": getattr(self, "_otp", None)}
        
class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'avatar', 'display_name', 'bio', 'email')
        read_only_fields = ('id', 'user')

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.display_name = validated_data.get('display_name', instance.display_name)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance