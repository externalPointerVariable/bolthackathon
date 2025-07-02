from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import CreateAPIView
from django.contrib.auth.models import User
from .models import UserSession, ChatSessions
from rest_framework.views import APIView
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from .serializers import RegisterSerializer, LoginSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer, UserProfileSerializer, UserSessionSerializer, UserSessionDetailSerializer, ChatSessionsSerializer

class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)     
        user = serializer.validated_data.get('user')
        data = serializer.validated_data
        return Response(data, status=status.HTTP_200_OK)
    
class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save(request)
            return Response(
                {
                    "message": "Password reset link and OTP sent successfully.",
                    "reset_link": result["reset_link"],
                    "otp": result["otp"]
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile = request.user.profile  # or request.user.userprofile if no related_name
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user_sessions = UserSession.objects.filter(user=request.user)
        serializer = UserSessionSerializer(user_sessions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = UserSessionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user_session = serializer.save()
            return Response(UserSessionSerializer(user_session).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            user_session = UserSession.objects.get(pk=pk, user=request.user)
        except UserSession.DoesNotExist:
            return Response({"error": "User session not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSessionDetailSerializer(user_session, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        try:
            user_session = UserSession.objects.get(pk=pk, user=request.user)
        except UserSession.DoesNotExist:
            return Response({"error": "User session not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSessionDetailSerializer(user_session, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            updated_session = serializer.save()
            return Response(UserSessionDetailSerializer(updated_session, context={'request': request}).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk, format=None):
        try:
            user_session = UserSession.objects.get(pk=pk, user=request.user)
        except UserSession.DoesNotExist:
            return Response({"error": "User session not found"}, status=status.HTTP_404_NOT_FOUND)

        user_session.delete()
        return Response({"message": "User session deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
class ChatSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, format=None):
        try:
            user_session = UserSession.objects.get(id=session_id, user=request.user)
        except UserSession.DoesNotExist:
            return Response({"error": "User session not found"}, status=status.HTTP_404_NOT_FOUND)

        chat_sessions = ChatSessions.objects.filter(session=user_session)
        serializer = ChatSessionsSerializer(chat_sessions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, session_id, format=None):
        try:
            user_session = UserSession.objects.get(id=session_id, user=request.user)
            chat_session = ChatSessions.objects.get(session=user_session)
        except (UserSession.DoesNotExist, ChatSessions.DoesNotExist):
            return Response({"error": "Chat session not found"}, status=status.HTTP_404_NOT_FOUND)

        request.data['session_id'] = session_id
        serializer = ChatSessionsSerializer(chat_session, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            instance, extra = serializer.save()
            return Response({
                "chat_session": ChatSessionsSerializer(instance).data,
                "response": extra["response"]
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
