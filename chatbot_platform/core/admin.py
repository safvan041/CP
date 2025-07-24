from django.contrib import admin
from .models import KnowledgeBase, ChatbotWidget # Removed UserProfile as it wasn't registered here

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'created_at',
        'is_embedded',   # Keep this if you still want a simple boolean check
        'status',        # <-- NEW: Display the status
        'widget_slug',
        'display_error_message_truncated' # <-- NEW: Custom method for error message
    )
    search_fields = ('title', 'user__username', 'widget_slug')
    list_filter = (
        'is_embedded',
        'status',        # <-- NEW: Filter by status
        'created_at'
    )
    ordering = ('-created_at',)

    # Optional: Add a custom method to display a truncated error message in list_display
    # This prevents very long error messages from cluttering the list view.
    def display_error_message_truncated(self, obj):
        if obj.status == 'failed' and obj.error_message:
            # Truncate to a reasonable length, e.g., 50 characters
            return obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
        return '-' # Display a dash if no error or not failed
    display_error_message_truncated.short_description = 'Error' # Column header


@admin.register(ChatbotWidget)
class ChatbotWidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)