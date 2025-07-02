from django.urls import path,  get_resolver
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.views import TokenRefreshView
from user.views import RegisterView, LoginView, PasswordResetView, PasswordResetConfirmView, UserProfileView, UserSessionView, UserSessionDetailView, ChatSessionsView

@api_view(["GET"])
def welcomeAPI(request):
    resolver = get_resolver()
    url_patterns = resolver.url_patterns
    endpoints = []

    def extract_patterns(patterns, prefix=""):
        for pattern in patterns:
            if hasattr(pattern, "pattern"):
                endpoints.append(prefix + str(pattern.pattern))
            if hasattr(pattern, "url_patterns"):
                extract_patterns(pattern.url_patterns, prefix + str(pattern.pattern))

    extract_patterns(url_patterns)

    return Response({"available_endpoints": endpoints})

urlpatterns = [
    path("", welcomeAPI, name="welcome"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password-reset-confirm/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    # JWT Token Refresh endpoint
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # User endpoint
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path("user-sessions/", UserSessionView.as_view(), name="user-session-list"),
    path("user-sessions/create/", UserSessionView.as_view(), name="create-user-session"),
    path("user-sessions/<int:pk>/", UserSessionDetailView.as_view(), name="user-session-detail"),
    path("user_sessions/<int:session_id>/chat-sessions/", ChatSessionsView.as_view(), name="chat-sessions-list"),
]