from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, UserSession, ChatSessions
from services.filetranslator import FileTranslator
from services.ocr import OCR
from services.chatbot import AzureChatbot
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
    
class UserSessionSerializer(serializers.ModelSerializer):
    pdf_image_urls = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            'id',
            'user',
            'session_name',
            'session_activity',
            'pdf_image_urls',
            'document_embeddings',
            'last_activity',
        ]
        read_only_fields = ['id', 'last_activity']

    def initial_document_embeddings(self, pdf_public_url, specifications):
        """
        Initialize document embeddings for the session.
        This method should be called after uploading the PDF and converting it to images.
        """
        file_translator = FileTranslator()
        bot = AzureChatbot()
        ocr_service = OCR()
        public_img_urls = file_translator.convert_pdf_to_images(pdf_public_url)
        ocr_texts = [ocr_service.extract_text_from_image(url) for url in public_img_urls]
        finalized_text = bot.transform_document(ocr_texts, specifications)
        return finalized_text
    
    def create():
        validated_data = self.validated_data
        user = validated_data['user']
        session_name = validated_data['session_name']
        session_activity = validated_data.get('specifications')
        pdf_public_url = validated_data.get('pdf_public_url')

        if pdf_public_url and session_activity:
            document_embeddings = self.initial_document_embeddings(pdf_public_url, session_activity)
        else:
            document_embeddings = None

        user_session = UserSession.objects.create(
            user=user,
            session_name=session_name,
            session_activity=session_activity,
            document_embeddings=document_embeddings
        )
        return user_session

    def update(self, instance, validated_data):
        instance.session_name = validated_data.get('session_name', instance.session_name)
        instance.session_activity = validated_data.get('session_activity', instance.session_activity)
        instance.save()
        return instance 