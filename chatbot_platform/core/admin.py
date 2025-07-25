# core/admin.py

from django.contrib import admin
# Ensure ChatbotUsage is imported as we will link to its data
from usage_analytics.models import ChatbotUsage # NEW: Import ChatbotUsage
from .models import KnowledgeBase, ChatbotWidget # REMINDER: KnowledgeBaseSourceFile is NOT here on this branch

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    """
    Admin configuration for KnowledgeBase model.
    Enhanced to show relevant details and link to usage stats.
    """
    list_display = (
        'title',
        'user',
        'created_at',
        'is_embedded',
        'display_total_messages_sent', # NEW: Custom method to show messages sent
        'display_last_message_at',     # NEW: Custom method to show last message time
        'widget_slug',
        'view_on_site_link',           # NEW: Custom method for direct link to widget
    )
    list_filter = (
        'user',              # Filter by KB owner
        'is_embedded',       # Filter by embedding status
        'created_at',        # Filter by creation date
    )
    search_fields = (
        'title',
        'user__username',
        'widget_slug',
    )
    ordering = ('-created_at',) # Default order

    # Custom method to display total messages sent from ChatbotUsage
    def display_total_messages_sent(self, obj):
        try:
            return obj.usage_stats.total_messages_sent # Access via related_name
        except ChatbotUsage.DoesNotExist:
            return 0 # Or '-' if no usage yet
    display_total_messages_sent.short_description = 'Messages Sent' # Column header

    # Custom method to display last message time from ChatbotUsage
    def display_last_message_at(self, obj):
        try:
            if obj.usage_stats.last_message_at:
                # Format the datetime for readability in admin
                return obj.usage_stats.last_message_at.strftime("%Y-%m-%d %H:%M")
            return 'Never'
        except ChatbotUsage.DoesNotExist:
            return 'Never'
    display_last_message_at.short_description = 'Last Message' # Column header

    # Custom method to create a clickable link to the chatbot widget
    def view_on_site_link(self, obj):
        if obj.widget_slug:
            # Construct the URL. Use a placeholder domain for admin display,
            # actual domain will depend on deploy (Codespaces/Prod).
            # This is just for admin convenience.
            # For local dev, it would be http://127.0.0.1:8000/chat/{slug}/
            # In a deployed admin, it needs the actual domain.
            # This is a basic example; for a real production admin, use django.contrib.sites or a custom setting.
            url = f"/chat/{obj.widget_slug}/" 
            return format_html('<a href="{}" target="_blank">Visit Widget</a>', url)
        return '-'
    view_on_site_link.short_description = 'Widget Link' # Column header
    view_on_site_link.allow_tags = True # Allow HTML in this column

# Ensure format_html is imported if using it
from django.utils.html import format_html


@admin.register(ChatbotWidget)
class ChatbotWidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

# REMINDER: ChatbotUsageAdmin is in usage_tracking/admin.py, not here.