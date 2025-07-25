# usage_tracking/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import KnowledgeBase # To get KBs owned by the user
from usage_analytics.models import ChatbotUsage # To get usage stats
from django.db.models import Prefetch # For optimized querying
import logging

logger = logging.getLogger(__name__)

@login_required
def usage_dashboard_view(request):
    """
    Displays the usage statistics for all Knowledge Bases owned by the logged-in user.
    """
    # Optimized query: Fetch Knowledge Bases and prefetch their related usage_stats
    # This avoids N+1 query problem when accessing usage_stats for each KB in the template
    user_knowledge_bases = KnowledgeBase.objects.filter(user=request.user).order_by('-created_at').prefetch_related('usage_stats')

    # If you want to filter out KBs with no usage or order by messages sent, you can
    # annotate or filter here, but prefetch_related is good for display.

    context = {
        'knowledge_bases': user_knowledge_bases,
        'has_usage_data': ChatbotUsage.objects.filter(knowledge_base__user=request.user).exists() # Check if user has any usage data
    }
    return render(request, 'usage_analytics/usage_dashboard.html', context)