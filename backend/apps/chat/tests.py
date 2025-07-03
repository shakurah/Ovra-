"""
Tests for the chat application.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.chat.models import ChatSession, ChatLog
from apps.chat.services import ChatService

User = get_user_model()


class ChatServiceTestCase(TestCase):
    """Test cases for ChatService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.session = ChatSession.objects.create(
            user=self.user,
            title='Test Session'
        )
        self.chat_service = ChatService()

    @patch('apps.chat.services.ChatService._process_regular_response')
    def test_process_question_regular(self, mock_process):
        """Test processing a regular (non-streaming) question."""
        # Mock service response
        mock_process.return_value = {
            'answer': 'Test response from AI',
            'citations': [],
            'retrieved_articles': [],
            'model': 'gpt-4o',
            'duration_ms': 1500,
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            }
        }

        # Test the service
        result = self.chat_service.process_question(
            question="¿Cuál es el tipo de IVA general?",
            session=self.session,
            stream=False
        )

        # Assertions
        self.assertIn('answer', result)
        self.assertIn('citations', result)
        self.assertIn('usage', result)
        self.assertEqual(result['answer'], "Test response from AI")
        self.assertEqual(result['usage']['total_tokens'], 150)

    @patch('apps.chat.services.ChatService._process_streaming_response')
    def test_process_question_streaming(self, mock_stream):
        """Test processing a streaming question."""
        # Mock streaming response generator
        def mock_generator():
            yield "Test "
            yield "streaming response"

        mock_stream.return_value = mock_generator()

        # Test the service
        result = self.chat_service.process_question(
            question="¿Cuál es el tipo de IVA general?",
            session=self.session,
            stream=True
        )

        # Collect streaming chunks
        chunks = list(result)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0], "Test ")
        self.assertEqual(chunks[1], "streaming response")

    def test_get_session_context(self):
        """Test getting session context."""
        # Create some chat logs
        ChatLog.objects.create(
            session=self.session,
            question="First question",
            answer="First answer",
            citations=[],
            duration_ms=1000,
            model_used="gpt-4o",
            retrieved_articles=[]
        )
        ChatLog.objects.create(
            session=self.session,
            question="Second question",
            answer="Second answer",
            citations=[],
            duration_ms=1200,
            model_used="gpt-4o",
            retrieved_articles=[]
        )

        context = self.chat_service.get_session_context(self.session, limit=2)

        # Should return messages in conversation format
        self.assertEqual(len(context), 4)  # 2 questions + 2 answers
        self.assertEqual(context[0]['role'], 'user')
        self.assertEqual(context[1]['role'], 'assistant')
        self.assertEqual(context[0]['content'], 'First question')
        self.assertEqual(context[1]['content'], 'First answer')

    def test_extract_citations(self):
        """Test citation extraction from text."""
        text = "Según el artículo 21 de la Ley del IVA, el tipo general es del 21%."
        citations = self.chat_service._extract_citations(text)

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]['article_num'], '21')
        self.assertIn('Ley del IVA', citations[0]['law'])


class ChatAPITestCase(APITestCase):
    """Test cases for Chat API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

        self.chat_url = reverse('chat:chat')
        self.stream_url = reverse('chat:chat-stream')

    def test_chat_requires_authentication(self):
        """Test that chat endpoint requires authentication."""
        response = self.client.post(self.chat_url, {
            'question': '¿Cuál es el tipo de IVA general?'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.chat.services.ChatService.process_question')
    def test_chat_success(self, mock_process):
        """Test successful chat request."""
        # Mock service response
        mock_process.return_value = {
            'answer': 'El tipo general del IVA es del 21%',
            'citations': [],
            'retrieved_articles': [],
            'model': 'gpt-4o',
            'duration_ms': 1500,
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            }
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.chat_url, {
            'question': '¿Cuál es el tipo de IVA general?'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.json())
        self.assertIn('answer', response.json()['data'])

    def test_chat_invalid_data(self):
        """Test chat with invalid data."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.chat_url, {
            'question': ''  # Empty question
        })

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_stream_requires_authentication(self):
        """Test that streaming endpoint requires authentication."""
        response = self.client.post(self.stream_url, {
            'question': '¿Cuál es el tipo de IVA general?'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatModelTestCase(TestCase):
    """Test cases for Chat models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_chat_session_creation(self):
        """Test creating a chat session."""
        session = ChatSession.objects.create(
            user=self.user,
            title='Test Session'
        )

        self.assertEqual(session.user, self.user)
        self.assertEqual(session.title, 'Test Session')
        self.assertTrue(session.is_active)
        self.assertIsNotNone(session.id)

    def test_chat_log_creation(self):
        """Test creating a chat log."""
        session = ChatSession.objects.create(
            user=self.user,
            title='Test Session'
        )

        chat_log = ChatLog.objects.create(
            session=session,
            question='Test question',
            answer='Test answer',
            citations=[],
            duration_ms=1000,
            model_used='gpt-4o',
            retrieved_articles=[]
        )

        self.assertEqual(chat_log.session, session)
        self.assertEqual(chat_log.question, 'Test question')
        self.assertEqual(chat_log.answer, 'Test answer')
        self.assertEqual(chat_log.duration_ms, 1000)

    def test_session_messages_relationship(self):
        """Test the relationship between session and messages."""
        session = ChatSession.objects.create(
            user=self.user,
            title='Test Session'
        )

        # Create multiple messages
        for i in range(3):
            ChatLog.objects.create(
                session=session,
                question=f'Question {i}',
                answer=f'Answer {i}',
                citations=[],
                duration_ms=1000,
                model_used='gpt-4o',
                retrieved_articles=[]
            )

        self.assertEqual(session.messages.count(), 3)
        self.assertEqual(session.messages.first().question, 'Question 2')  # Most recent first
