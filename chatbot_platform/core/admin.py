from django.contrib import admin
from .models import  KnowledgeBase, ChatbotWidget



@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'is_embedded', 'embedded', 'widget_slug')
    search_fields = ('title', 'user__username', 'widget_slug')
    list_filter = ('is_embedded', 'embedded', 'created_at')
    ordering = ('-created_at',)


@admin.register(ChatbotWidget)
class ChatbotWidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
