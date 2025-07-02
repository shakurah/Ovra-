"""
Views for the chat application.
"""
import time
import logging
from typing import Optional
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from apps.common.responses import APIResponse
from apps.chat.models import ChatLog, ChatSession, CostMetric
from apps.chat.serializers import (
    ChatRequestSerializer, ChatResponseSerializer, ChatSessionSerializer,
    ChatLogSerializer, ChatStatsSerializer, RatingUpdateSerializer
)
from apps.chat.services import ChatService
from apps.core.exceptions import OpenAIException, VectorStoreException

logger = logging.getLogger(__name__)


@method_decorator(ratelimit(key='ip', rate='60/m', method='POST'), name='dispatch')
class ChatAPIView(APIView):
    """
    Main chat endpoint for asking tax law questions.
    """
    permission_classes = [AllowAny]  # Change to IsAuthenticated for production
    
    def post(self, request):
        """
        Process a chat request and return AI-generated response.
        """
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                errors=serializer.errors,
                message="Invalid request data"
            )
        
        validated_data = serializer.validated_data
        start_time = time.time()
        
        try:
            # Get or create session
            session = None
            if validated_data.get('session_id'):
                try:
                    session = ChatSession.objects.get(
                        id=validated_data['session_id'],
                        is_active=True
                    )
                except ChatSession.DoesNotExist:
                    return APIResponse.not_found(
                        message="Session not found or inactive"
                    )
            else:
                # Create new session if not provided
                session = ChatSession.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    title=validated_data['question'][:50] + "..."
                )
            
            # Process the chat request
            chat_service = ChatService()
            result = chat_service.process_question(
                question=validated_data['question'],
                session=session,
                law_filter=validated_data.get('law_filter'),
                stream=validated_data.get('stream', False)
            )
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Save chat log and cost metrics in a transaction
            with transaction.atomic():
                chat_log = ChatLog.objects.create(
                    session=session,
                    question=validated_data['question'],
                    answer=result['answer'],
                    citations=result['citations'],
                    duration_ms=duration_ms,
                    model_used=result.get('model', 'gpt-4o'),
                    retrieved_articles=result.get('retrieved_articles', [])
                )
                
                # Save cost metrics
                if 'usage' in result:
                    usage = result['usage']
                    cost_eur = chat_service.calculate_cost(usage)
                    CostMetric.objects.create(
                        chat_log=chat_log,
                        prompt_tokens=usage.get('prompt_tokens', 0),
                        completion_tokens=usage.get('completion_tokens', 0),
                        embedding_tokens=usage.get('embedding_tokens', 0),
                        cost_eur=cost_eur['total'],
                        prompt_cost_eur=cost_eur['prompt'],
                        completion_cost_eur=cost_eur['completion'],
                        embedding_cost_eur=cost_eur['embedding']
                    )
            
            # Prepare response
            response_data = ChatResponseSerializer({
                'id': chat_log.id,
                'question': chat_log.question,
                'answer': chat_log.answer,
                'citations': result['citations'],
                'session_id': session.id,
                'created_at': chat_log.created_at,
                'duration_ms': duration_ms,
                'model_used': chat_log.model_used
            }).data
            
            return APIResponse.success(
                data=response_data,
                message="Response generated successfully"
            )
            
        except OpenAIException as e:
            logger.error(f"OpenAI error: {str(e)}")
            return APIResponse.error(
                message="Error processing question with AI service",
                error_code="OPENAI_ERROR",
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except VectorStoreException as e:
            logger.error(f"Vector store error: {str(e)}")
            return APIResponse.error(
                message="Error searching for relevant legal information",
                error_code="VECTOR_STORE_ERROR",
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in chat: {str(e)}", exc_info=True)
            return APIResponse.server_error(
                message="Unexpected error processing question"
            )


class ChatSessionListView(ListAPIView):
    """
    List user's chat sessions.
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get sessions for the authenticated user."""
        return ChatSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-updated_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to use APIResponse."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return APIResponse.paginated(
                data=serializer.data,
                total=queryset.count(),
                page=int(request.GET.get('page', 1)),
                page_size=int(request.GET.get('page_size', 20)),
                message="Sessions retrieved successfully"
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(
            data=serializer.data,
            message="Sessions retrieved successfully"
        )


class ChatSessionDetailView(RetrieveAPIView):
    """
    Retrieve a specific chat session with its messages.
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get sessions for the authenticated user."""
        return ChatSession.objects.filter(
            user=self.request.user,
            is_active=True
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to include messages and use APIResponse."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            # Get messages for this session
            messages = ChatLog.objects.filter(
                session=instance
            ).order_by('created_at')
            
            messages_data = ChatLogSerializer(messages, many=True).data
            
            response_data = {
                'session': serializer.data,
                'messages': messages_data
            }
            
            return APIResponse.success(
                data=response_data,
                message="Session retrieved successfully"
            )
        except ChatSession.DoesNotExist:
            return APIResponse.not_found(
                message="Session not found"
            )


class ChatHistoryView(ListAPIView):
    """
    Get chat history for the authenticated user.
    """
    serializer_class = ChatLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get chat logs for the authenticated user."""
        return ChatLog.objects.filter(
            session__user=self.request.user
        ).select_related('session').order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to use APIResponse."""
        queryset = self.get_queryset()
        
        # Apply filters
        session_id = request.GET.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        date_from = request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return APIResponse.paginated(
                data=serializer.data,
                total=queryset.count(),
                page=int(request.GET.get('page', 1)),
                page_size=int(request.GET.get('page_size', 20)),
                message="History retrieved successfully"
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(
            data=serializer.data,
            message="History retrieved successfully"
        )


class UpdateChatRatingView(APIView):
    """
    Update the rating for a specific chat.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, chat_id):
        """Update chat rating."""
        serializer = RatingUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                errors=serializer.errors,
                message="Invalid rating data"
            )
        
        try:
            chat_log = ChatLog.objects.get(
                id=chat_id,
                session__user=request.user
            )
            
            chat_log.user_rating = serializer.validated_data['rating']
            chat_log.save(update_fields=['user_rating'])
            
            return APIResponse.success(
                message="Rating updated successfully",
                data={'rating': chat_log.user_rating}
            )
            
        except ChatLog.DoesNotExist:
            return APIResponse.not_found(
                message="Chat not found"
            )
