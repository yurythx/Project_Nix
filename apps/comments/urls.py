from django.urls import path, include
from django.views.decorators.cache import cache_page

from .views import (
    # Comment Views
    CommentListView, CommentDetailView, CommentCreateView,
    CommentUpdateView, CommentDeleteView, CommentReactionView,
    CommentSearchView, CommentThreadView, LoadMoreCommentsView,
    
    # Moderation Views
    ModerationQueueView, ModerationDetailView, ModerationActionView,
    BulkModerationView, ModerationStatsView, ModerationConfigView,
    AssignModerationView, ModerationHistoryView, SpamDetectionView,
    ReportedCommentsView,
    
    # Notification Views
    NotificationListView, NotificationDetailView, MarkNotificationReadView,
    MarkAllNotificationsReadView, DeleteNotificationView,
    NotificationPreferencesView, NotificationStatsView,
    NotificationSummaryView, NotificationAPIView as NotificationAJAXView,
    TestNotificationView, CleanupNotificationsView,
    
    # API Views
    CommentAPIView, CommentDetailAPIView, CommentReactionAPIView,
    CommentReportAPIView, CommentPinAPIView, CommentStatsAPIView,
    CommentSearchAPIView, CommentThreadAPIView, NotificationAPIView,
    NotificationMarkReadAPIView,
)

app_name = 'comments'

# URLs principais de comentários
comment_patterns = [
    path('', CommentListView.as_view(), name='comment_list'),
    path('create/', CommentCreateView.as_view(), name='comment_create'),
    path('search/', CommentSearchView.as_view(), name='comment_search'),
    path('load-more/', LoadMoreCommentsView.as_view(), name='load_more_comments'),
    
    path('<uuid:pk>/', CommentDetailView.as_view(), name='comment_detail'),
    path('<uuid:pk>/edit/', CommentUpdateView.as_view(), name='comment_edit'),
    path('<uuid:pk>/delete/', CommentDeleteView.as_view(), name='comment_delete'),
    path('<uuid:pk>/reaction/', CommentReactionView.as_view(), name='comment_reaction'),
    path('<uuid:pk>/thread/', CommentThreadView.as_view(), name='comment_thread'),
]

# URLs de moderação
moderation_patterns = [
    path('', ModerationQueueView.as_view(), name='moderation_queue'),
    path('stats/', ModerationStatsView.as_view(), name='moderation_stats'),
    path('config/', ModerationConfigView.as_view(), name='moderation_config'),
    path('history/', ModerationHistoryView.as_view(), name='moderation_history'),
    path('spam-detection/', SpamDetectionView.as_view(), name='spam_detection'),
    path('reported/', ReportedCommentsView.as_view(), name='reported_comments'),
    path('bulk-action/', BulkModerationView.as_view(), name='bulk_moderation'),
    
    path('<int:pk>/', ModerationDetailView.as_view(), name='moderation_detail'),
    path('<int:pk>/action/', ModerationActionView.as_view(), name='moderation_action'),
    path('<int:pk>/assign/', AssignModerationView.as_view(), name='assign_moderation'),
]

# URLs de notificações
notification_patterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('preferences/', NotificationPreferencesView.as_view(), name='notification_preferences'),
    path('stats/', NotificationStatsView.as_view(), name='notification_stats'),
    path('summary/', NotificationSummaryView.as_view(), name='notification_summary'),
    path('ajax/', NotificationAJAXView.as_view(), name='notification_ajax'),
    path('mark-all-read/', MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
    path('cleanup/', CleanupNotificationsView.as_view(), name='cleanup_notifications'),
    path('test/', TestNotificationView.as_view(), name='test_notification'),
    
    path('<uuid:pk>/', NotificationDetailView.as_view(), name='notification_detail'),
    path('<uuid:pk>/mark-read/', MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('<uuid:pk>/delete/', DeleteNotificationView.as_view(), name='delete_notification'),
]

# URLs da API
api_patterns = [
    # Comentários
    path('comments/', CommentAPIView.as_view(), name='api_comments'),
    path('comments/search/', CommentSearchAPIView.as_view(), name='api_comment_search'),
    path('comments/stats/', CommentStatsAPIView.as_view(), name='api_comment_stats'),
    path('comments/<uuid:comment_id>/', CommentDetailAPIView.as_view(), name='api_comment_detail'),
    path('comments/<uuid:comment_id>/reaction/', CommentReactionAPIView.as_view(), name='api_comment_reaction'),
    path('comments/<uuid:comment_id>/report/', CommentReportAPIView.as_view(), name='api_comment_report'),
    path('comments/<uuid:comment_id>/pin/', CommentPinAPIView.as_view(), name='api_comment_pin'),
    path('comments/<uuid:comment_id>/thread/', CommentThreadAPIView.as_view(), name='api_comment_thread'),
    
    # Notificações
    path('notifications/', NotificationAPIView.as_view(), name='api_notifications'),
    path('notifications/mark-read/', NotificationMarkReadAPIView.as_view(), name='api_mark_all_notifications_read'),
    path('notifications/<uuid:notification_id>/mark-read/', NotificationMarkReadAPIView.as_view(), name='api_mark_notification_read'),
]

# URLs principais
urlpatterns = [
    # Comentários
    path('', include(comment_patterns)),
    
    # Moderação (apenas para usuários com permissão)
    path('moderation/', include(moderation_patterns)),
    
    # Notificações
    path('notifications/', include(notification_patterns)),
    
    # API
    path('api/', include(api_patterns)),
    
    # URLs específicas para objetos
    path('for/<int:content_type_id>/<int:object_id>/', 
         CommentListView.as_view(), 
         name='comments_for_object'),
    
    path('for/<int:content_type_id>/<int:object_id>/create/', 
         CommentCreateView.as_view(), 
         name='create_comment_for_object'),
    
    # URLs com cache para performance
    path('popular/', 
         cache_page(60 * 15)(CommentListView.as_view(template_name='comments/popular.html')), 
         name='popular_comments'),
    
    path('recent/', 
         cache_page(60 * 5)(CommentListView.as_view(template_name='comments/recent.html')), 
         name='recent_comments'),
]

# URLs para desenvolvimento/debug (apenas em DEBUG=True)
from django.conf import settings
if settings.DEBUG:
    from django.views.generic import TemplateView
    
    debug_patterns = [
        path('debug/websocket-test/', 
             TemplateView.as_view(template_name='comments/debug/websocket_test.html'), 
             name='websocket_test'),
        
        path('debug/notification-test/', 
             TestNotificationView.as_view(), 
             name='debug_notification_test'),
    ]
    
    urlpatterns += [
        path('debug/', include(debug_patterns)),
    ]