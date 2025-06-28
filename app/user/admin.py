from django.contrib import admin
from .models import UserProfile, ChatSessions, UserSession

# Register your models here.
admin.site.register([UserProfile,
                     ChatSessions,
                     UserSession,
                     ])