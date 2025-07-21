from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default="User")  # Future-proof for roles like admin/user

    def __str__(self):
        return self.user.username


class KnowledgeBase(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),       
        ('processing', 'Processing'),   
        ('completed', 'Completed'),     
        ('failed', 'Failed'),           
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="knowledge_bases/")  # Use default storage
    created_at = models.DateTimeField(auto_now_add=True)
   

    is_embedded = models.BooleanField(default=False)
    widget_slug = models.SlugField(unique=True, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded', # Default status when a new KB is created
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


class ChatbotWidget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    embed_code = models.TextField(blank=True, null=True)  # Generated JS for embedding
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
