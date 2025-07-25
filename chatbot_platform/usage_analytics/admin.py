# usage_tracking/admin.py

from django.contrib import admin
from .models import ChatbotUsage # Import the ChatbotUsage model

@admin.register(ChatbotUsage)
class ChatbotUsageAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatbotUsage model.
    Allows viewing, filtering, and searching usage statistics.
    """
    list_display = (
        'knowledge_base_title',  # Custom method to display KB title
        'total_messages_sent',
        'last_message_at',
        'updated_at',
    )
    list_filter = (
        'knowledge_base__user', # Filter by the user who owns the Knowledge Base
        'updated_at',          # Filter by last update time
    )
    search_fields = (
        'knowledge_base__title',          # Search by Knowledge Base title
        'knowledge_base__user__username', # Search by Knowledge Base owner's username
    )
    ordering = ('-updated_at',) # Default order by most recently updated usage stats

    # Custom method to display the KnowledgeBase title in list_display
    # This retrieves the title from the related KnowledgeBase object
    def knowledge_base_title(self, obj):
        return obj.knowledge_base.title
    knowledge_base_title.short_description = 'Knowledge Base' # Sets the column header in admin