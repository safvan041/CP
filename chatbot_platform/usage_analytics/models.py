# usage_tracking/models.py

from django.db import models
from core.models import KnowledgeBase # Import KnowledgeBase from the core app
from django.contrib.auth.models import User # For linking to users if needed beyond KB owner
from django.utils import timezone # For timezone.now()

class ChatbotUsage(models.Model):
    """
    Tracks usage statistics for a specific KnowledgeBase.
    This model will hold message counts and timestamps.
    """
    knowledge_base = models.OneToOneField( # Use OneToOneField for simple 1:1 usage stats per KB
        KnowledgeBase,
        on_delete=models.CASCADE, # If KB is deleted, usage stats are deleted
        related_name='usage_stats', # Allows kb_instance.usage_stats
        primary_key=True, # Makes this table's PK also the FK to KnowledgeBase, useful for 1:1
        help_text="The Knowledge Base these usage statistics belong to."
    )
    
    total_messages_sent = models.PositiveIntegerField(default=0, help_text="Total number of messages sent to this chatbot.")
    last_message_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of the last message sent to this chatbot.")
    
    updated_at = models.DateTimeField(auto_now=True, help_text="Last time these usage statistics were updated.")

    def __str__(self):
        return f"Usage for KB: {self.knowledge_base.title} ({self.total_messages_sent} msgs)"

    class Meta:
        verbose_name_plural = "Chatbot Usage Statistics"