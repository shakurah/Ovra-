from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.db import transaction
from django.shortcuts import get_object_or_404
from uuid import uuid4
import logging

from apps.widget.models import UserEngagement
from apps.chat.models import ChatLog, ChatSession
from apps.chat.services import ChatService
from apps.common.responses import APIResponse
from apps.widget.serializers import (
    WidgetUserSerializer,
    WidgetChatRequestSerializer,
    WidgetChatResponseSerializer,
    WidgetFeedbackSerializer
)

logger = logging.getLogger(__name__)


class WidgetAnonRateThrottle(AnonRateThrottle):
    """Custom rate throttle for widget anonymous users."""
    rate = '30/minute'  # More restrictive for anonymous users


class WidgetRegisterView(APIView):
    """
    Register widget user with email.
    This endpoint is called when user first provides their email in the widget.
    """
    permission_classes = [AllowAny]
    throttle_classes = [WidgetAnonRateThrottle]
    
    def post(self, request):
        """Register or update widget user."""
        serializer = WidgetUserSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(
                errors=serializer.errors,
                message="Invalid registration data"
            )
        
        # Add source website from request
        if 'source_website' not in serializer.validated_data:
            # Get origin from request headers
            origin = request.META.get('HTTP_ORIGIN', '')
            referer = request.META.get('HTTP_REFERER', '')
            serializer.validated_data['source_website'] = origin or referer
        
        user_engagement = serializer.save()
        
        return APIResponse.success(
            data={
                'email': user_engagement.email,
                'user_id': str(user_engagement.id)
            },
            message='Successfully registered. You can now ask questions.'
        )


class WidgetChatView(APIView):
    """
    Widget chat endpoint.
    Allows users to ask questions after providing their email.
    """
    permission_classes = [AllowAny]
    throttle_classes = [WidgetAnonRateThrottle]
    
    def post(self, request):
        """Process widget chat request."""
        serializer = WidgetChatRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(
                errors=serializer.errors,
                message="Invalid chat request data"
            )
        
        data = serializer.validated_data
        email = data['email']
        question = data['question']
        session_id = data.get('session_id')
        
        # Check if user is registered
        try:
            user_engagement = UserEngagement.objects.get(email=email)
        except UserEngagement.DoesNotExist:
            return APIResponse.forbidden(
                message='Please register with your email first.',
                error_code='USER_NOT_REGISTERED'
            )
        
        # Check if user is active
        if not user_engagement.is_active:
            return APIResponse.forbidden(
                message='Your account has been deactivated.',
                error_code='USER_DEACTIVATED'
            )
        
        # Get or create session for this email
        if session_id:
            try:
                session = ChatSession.objects.get(
                    id=session_id,
                    user__isnull=True  # Widget sessions don't have authenticated users
                )
            except ChatSession.DoesNotExist:
                session = None
        else:
            session = None
        
        if not session:
            # Create new anonymous session
            session = ChatSession.objects.create(
                title=f"Widget Chat - {email}",
                user=None,  # No authenticated user
                is_active=True
            )
        
        try:
            # Initialize chat service and get response
            chat_service = ChatService()
            
            with transaction.atomic():
                # Create chat log entry
                chat_log = ChatLog.objects.create(
                    id=uuid4(),
                    session=session,
                    question=question,
                    answer="",  # Will be updated
                    citations=[],
                    duration_ms=0,
                    model_used=chat_service.model,
                    retrieved_articles=[]
                )
                
                # Get AI response
                response_data = chat_service.process_question(
                    question=question,
                    session=session
                )
                
                # Update chat log with response
                chat_log.answer = response_data['answer']
                chat_log.citations = response_data.get('citations', [])
                chat_log.duration_ms = response_data.get('duration_ms', 0)
                chat_log.retrieved_articles = response_data.get('retrieved_articles', [])
                chat_log.save()
                
                # Update user engagement metrics
                user_engagement.increment_questions()
                
                # Prepare response data
                response_data = {
                    'answer': chat_log.answer,
                    'citations': chat_log.citations,
                    'session_id': str(session.id),
                    'chat_id': str(chat_log.id),
                    'duration_ms': chat_log.duration_ms
                }
                
                return APIResponse.success(
                    data=response_data,
                    message='Question answered successfully'
                )
                
        except Exception as e:
            logger.error(f"Widget chat error: {str(e)}", exc_info=True)
            return APIResponse.server_error(
                message='An error occurred while processing your question.',
                error_code='CHAT_PROCESSING_ERROR'
            )


class WidgetFeedbackView(APIView):
    """
    Widget feedback endpoint.
    Allows users to provide feedback on responses.
    """
    permission_classes = [AllowAny]
    throttle_classes = [WidgetAnonRateThrottle]
    
    def post(self, request):
        """Process feedback for a chat response."""
        serializer = WidgetFeedbackSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(
                errors=serializer.errors,
                message="Invalid feedback data"
            )
        
        data = serializer.validated_data
        chat_id = data['chat_id']
        
        try:
            chat_log = ChatLog.objects.get(id=chat_id)
            
            # Update rating if provided
            if 'rating' in data:
                chat_log.user_rating = data['rating']
                chat_log.save(update_fields=['user_rating'])
            
            # Handle helpful feedback (convert to rating)
            if 'helpful' in data:
                # Convert helpful boolean to rating
                if data['helpful']:
                    chat_log.user_rating = 5
                else:
                    chat_log.user_rating = 2
                chat_log.save(update_fields=['user_rating'])
            
            return APIResponse.success(
                data={'chat_id': str(chat_id)},
                message='Thank you for your feedback!'
            )
            
        except ChatLog.DoesNotExist:
            return APIResponse.not_found(
                message='Chat not found.',
                error_code='CHAT_NOT_FOUND'
            )
        except Exception as e:
            logger.error(f"Widget feedback error: {str(e)}", exc_info=True)
            return APIResponse.server_error(
                message='Failed to save feedback.',
                error_code='FEEDBACK_SAVE_ERROR'
            )