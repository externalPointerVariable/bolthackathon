from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, UserSession, ChatSessions
from services.filetranslator import FileTranslator
from services.chatbot import AzureChatbot
from django.core.mail import send_mail
import random
import json
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
            'session_keywords',
            'pdf_image_urls',
            'document_embeddings',
            'last_activity',
        ]
        read_only_fields = ['id', 'last_activity', 'user', 'session_name']

    def get_pdf_image_urls(self, obj):
        try:
            return json.loads(obj.pdf_image_urls or "[]")
        except (TypeError, ValueError):
            return []

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        pdf_public_url = request.data.get('pdf_public_url')
        specifications = request.data.get('specifications', {})

        if not pdf_public_url:
            raise serializers.ValidationError({"pdf_public_url": "This field is required."})

        file_translator = FileTranslator()
        bot = AzureChatbot()

        try:
            public_img_urls = file_translator.pdf_to_images_and_store(pdf_public_url)
            ocr_texts = [bot.image_to_text(url) for url in public_img_urls]

            finalized_text = bot.transform_document(ocr_texts, specifications) if specifications else None
            session_name = bot.create_session_name(finalized_text or "\n".join(ocr_texts))
            session_keywords = bot.keywords_extraction(ocr_texts) if ocr_texts else None

            user_session = UserSession.objects.create(
                user=user,
                session_name=session_name,
                session_activity=specifications,  # JSONField can take dict directly
                session_keywords=session_keywords,
                pdf_image_urls=json.dumps(public_img_urls),
                ocr_text="\n".join(ocr_texts) if ocr_texts else "",
                document_embeddings=finalized_text or {}
            )

            ChatSessions.objects.create(
                session=user_session,
                chat_history=[]
            )

            return user_session

        except Exception as e:
            raise serializers.ValidationError({"error": f"Failed to create session: {str(e)}"})

    def update(self, instance, validated_data):
        instance.session_name = validated_data.get('session_name', instance.session_name)
        instance.session_activity = validated_data.get('session_activity', instance.session_activity)
        instance.save()
        return instance

class UserSessionDetailSerializer(serializers.ModelSerializer):
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
        read_only_fields = ['id', 'last_activity', 'user']

    def update(self, instance, validated_data):
        bot = AzureChatbot()

        instance.session_name = validated_data.get('session_name', instance.session_name)
        instance.session_activity = validated_data.get('session_activity', instance.session_activity)
        ocr_text = instance.ocr_text or validated_data.get('ocr_text', None)
        document_embeddings = bot.transform_document(ocr_text, instance.session_activity)
        instance.document_embeddings = document_embeddings
        instance.save()
        return instance

class ChatSessionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSessions
        fields = ['id', 'session', 'chat_history']
        read_only_fields = ['id', 'session', 'chat_history']

    def update(self, instance, validated_data):
        request = self.context['request']
        user_query = request.data.get('user_query')
        session_id = request.data.get('session_id')

        if not user_query:
            raise serializers.ValidationError({"user_query": "This field is required."})
        if not session_id:
            raise serializers.ValidationError({"session_id": "This field is required."})

        try:
            session_data = UserSession.objects.get(id=session_id, user=request.user)
        except UserSession.DoesNotExist:
            raise serializers.ValidationError({"error": "Invalid session or not authorized."})

        context_doc = session_data.ocr_text
        if not context_doc:
            raise serializers.ValidationError({"error": "Context document is required for chatbot interaction."})

        chat_history = instance.chat_history or []

        # Get response from chatbot
        bot = AzureChatbot()
        response = bot.rag_chatbot(user_query, context_doc, prev_chat_context=chat_history[-15:])

        # Append new entry to chat history
        chat_history.append({
            "user_query": user_query,
            "response": response
        })

        # Save updated history
        instance.chat_history = chat_history
        instance.save()

        # Return both instance and response for custom use
        return [instance, {"response": response}]
