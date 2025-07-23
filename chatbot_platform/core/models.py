from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default="User")  # Future-proof for roles like admin/user

    def __str__(self):
        return self.user.username


class KnowledgeBase(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),       # KB record created, files might be uploaded but not processed
        ('processing', 'Processing'),   # KB files are being processed for embedding
        ('completed', 'Completed'),     # All files for this KB processed, embedding finished successfully
        ('failed', 'Failed'),           # Processing/embedding failed for this KB
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    is_embedded = models.BooleanField(default=False, help_text="True if this Knowledge Base's embeddings are generated and stored.")
    widget_slug = models.CharField(max_length=10, unique=True, null=True, blank=True)

    status = models.CharField( 
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded',
        help_text="Current processing status of the knowledge base embeddings."
    )
    error_message = models.TextField( 
        blank=True,
        null=True,
        help_text="Stores any error messages if embedding fails."
    )

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    class Meta:
        verbose_name_plural = "Knowledge Bases"


# --- NEW MODEL: KnowledgeBaseSourceFile ---
class KnowledgeBaseSourceFile(models.Model):
    """
    Represents an individual source file that contributes to a KnowledgeBase.
    """
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.CASCADE,
        related_name='source_files', # Allows kb_instance.source_files.all()
        help_text="The Knowledge Base this file belongs to."
    )
    file = models.FileField(
        upload_to="kb_source_files/", # New, dedicated media upload directory for source files
        help_text="The actual file content for the knowledge base."
    )
    filename = models.CharField(max_length=255, help_text="Original filename for display.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} for KB: {self.knowledge_base.title}"

    class Meta:
        verbose_name_plural = "Knowledge Base Source Files"
        ordering = ['-uploaded_at']



class ChatbotWidget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    embed_code = models.TextField(blank=True, null=True)  # Generated JS for embedding
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
