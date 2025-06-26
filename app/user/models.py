from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

user = get_user_model()

class UserProfile(models.Model):
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    user = models.OneToOneField(user, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=255, blank=True, null=True, default=None)
    bio = models.TextField(blank=True, null=True)
    email =  models.EmailField(unique=True, blank=True, null=True)


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_name = models.CharField(max_length=40, unique=True)
    session_activity = models.TextField(blank=True, null=True)
    pdf_image_urls = models.TextField(blank=True, null=True)
    document_embeddings = models.JSONField(blank=True, null=True)
    last_activity = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.session_name} - {self.last_activity.strftime('%Y-%m-%d %H:%M:%S')}"

    def __repr__(self):
        return f"<UserSession user={self.user.username} session_name={self.session_name}>"

    class Meta:
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ['-last_activity']

class ChatSessions(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='chat_sessions')
    chat_history = models.JSONField(blank=True, null=True)