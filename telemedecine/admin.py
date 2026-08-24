from django.contrib import admin
# telemedecine/admin.py
from django.contrib import admin
from .models import SessionTelemedecine, Message

admin.site.register(SessionTelemedecine)
admin.site.register(Message)
# Register your models here.
