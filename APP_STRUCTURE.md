# Ovra AI Tax Assistant - Complete App Structure

## 🏗️ Project Overview

**Ovra AI Tax Assistant** is an AI-powered legal chatbot system that helps freelancers and professionals in arts/cultural sectors with tax questions. Built with Django (backend) and Next.js (frontend). The system defaults to English with Spanish as a secondary language.

## 📁 Root Directory Structure

```
ovra_ai/
├── backend/                 # Django REST API backend
├── frontend/               # Next.js React frontend
├── scripts/               # Deployment and automation scripts
├── test_integration.js    # Integration testing
├── APP_STRUCTURE.md      # This documentation
└── README.md             # Project documentation
```

## 🔧 Backend Structure (Django)

### Core Architecture
- **Framework**: Django 5.0+ with Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: JWT with djangorestframework-simplejwt
- **API Version**: v1 (`/api/v1/`)
- **Port**: 8000

### Directory Structure
```
backend/
├── ovra_backend/          # Main Django project
│   ├── settings.py       # Django settings
│   ├── urls.py          # Main URL configuration
│   ├── wsgi.py          # WSGI application
│   └── asgi.py          # ASGI application (WebSockets)
├── apps/                 # Django applications
│   ├── common/          # Common utilities and responses
│   │   ├── responses.py # APIResponse class for consistent responses
│   │   └── exceptions.py # Custom exception handlers
│   ├── core/            # User management and authentication
│   │   ├── models.py    # Custom User model (email-based auth)
│   │   ├── serializers.py # User serializers
│   │   ├── views.py     # Authentication views
│   │   └── urls.py      # Core URL patterns
│   ├── legal/           # Legal document management
│   ├── chat/            # AI chat functionality
│   └── embeddings/      # Vector embeddings for legal docs
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── db.sqlite3           # SQLite database (development)
```

### Key Backend Components

#### User Model (apps/core/models.py)
- **Custom User Model**: Extends AbstractUser
- **Primary Key**: Email (not username)
- **Fields**: email, full_name, profile_picture, preferred_language, created_at, updated_at, last_login_ip
- **Authentication**: Email-based login

#### API Endpoints
```
/api/v1/health/                    # Health check
/api/v1/auth/login/               # User login
/api/v1/auth/register/            # User registration
/api/v1/auth/logout/              # User logout
/api/v1/auth/token/refresh/       # Token refresh
/api/v1/user/profile/             # User profile management
/api/v1/chat/message/             # AI chat endpoint
/api/v1/legal/documents/          # Legal document access
```

#### Response Format
All API responses use consistent format via APIResponse class:
```json
{
  "code": 200,
  "is_success": true,
  "message": "Success message",
  "data": { ... }
}
```

## 🎨 Frontend Structure (Next.js)

### Core Architecture
- **Framework**: Next.js 15.2.4 with TypeScript
- **UI Library**: Shadcn/UI + Radix UI
- **Styling**: Tailwind CSS
- **State Management**: React Context + Custom Hooks
- **Port**: 3000

### Directory Structure
```
frontend/
├── app/                  # Next.js App Router
│   ├── globals.css      # Global styles
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Home page
│   ├── login/           # Login page
│   ├── signup/          # Registration page
│   ├── chat/            # Chat interface
│   └── profile/         # User profile
├── components/          # React components
│   ├── ui/             # Shadcn/UI components
│   ├── auth/           # Authentication components
│   ├── chat/           # Chat components
│   └── layout/         # Layout components
├── contexts/           # React contexts
│   └── auth-context.tsx # Authentication context
├── lib/               # Utilities and services
│   ├── services/      # API services (MODULAR ARCHITECTURE)
│   │   ├── base.service.ts    # Base HTTP service
│   │   ├── auth.service.ts    # Authentication service
│   │   ├── user.service.ts    # User management service
│   │   ├── chat.service.ts    # AI chat service
│   │   ├── config.ts          # Service configuration
│   │   ├── examples.ts        # Usage examples
│   │   ├── index.ts           # Central exports
│   │   └── README.md          # Service documentation
│   ├── api.ts         # Main API exports (legacy compatibility)
│   └── utils.ts       # Utility functions
├── utils/             # Additional utilities
│   └── api.ts         # API error handling utilities
├── package.json       # Node.js dependencies
├── tsconfig.json      # TypeScript configuration
├── tailwind.config.ts # Tailwind configuration
└── next.config.js     # Next.js configuration
```

### 🔗 API Services Architecture (MODULAR)

#### Service Hierarchy
```
BaseApiService (base.service.ts)
├── AuthService (auth.service.ts)
├── UserService (user.service.ts)
└── ChatService (chat.service.ts)
```

#### BaseApiService Features
- HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Authentication header management
- Response/error handling
- Token management utilities
- SSR compatibility

#### AuthService Methods
- `login(credentials)` - User authentication
- `register(userData)` - User registration
- `logout()` - User logout
- `refreshToken()` - Token refresh
- `verifyToken()` - Token validation
- `isAuthenticated()` - Auth status check
- `getCurrentUser()` - Get current user
- `autoRefreshToken()` - Auto token refresh

#### UserService Methods
- `getProfile()` - Get user profile
- `updateProfile(data)` - Update profile
- `uploadProfilePicture(file)` - Upload avatar
- `getUserStats()` - Get usage statistics
- `getPreferences()` - Get user preferences
- `updatePreferences(prefs)` - Update preferences

#### ChatService Methods
- `sendMessage(request)` - Send AI message
- `startConversation(message)` - New conversation
- `continueConversation(id, message)` - Continue chat
- `getConversation(id)` - Get chat history
- `getConversations()` - List conversations
- `searchConversations(query)` - Search chats
- `getSuggestedQuestions()` - Get AI suggestions

### Import Patterns
```typescript
// Recommended (modular)
import { authService, userService, chatService } from '@/lib/services'

// Legacy compatibility
import { apiService } from '@/lib/api' // Same as authService

// Direct service import
import { authService } from '@/lib/services/auth.service'
```

## 🚀 Deployment & Scripts

### Scripts Directory
```
scripts/
├── install_dependencies.sh  # System dependencies
├── setup_backend.sh         # Django setup
├── setup_frontend.sh        # Next.js setup
├── nginx_config.sh          # Nginx configuration
├── start_services.sh        # Start all services
├── stop_services.sh         # Stop all services
└── restart_services.sh      # Restart all services
```

### Service Ports
- **Frontend (Next.js)**: 3000
- **Backend (Django)**: 8000
- **Database (PostgreSQL)**: 5432 (production)
- **Redis**: 6379
- **Nginx**: 80/443 (production)

## 🔐 Authentication Flow

1. **Registration**: POST `/api/v1/auth/register/`
2. **Login**: POST `/api/v1/auth/login/`
3. **Token Storage**: localStorage (access_token, refresh_token, user)
4. **API Calls**: Authorization: Bearer {access_token}
5. **Token Refresh**: Automatic via `autoRefreshToken()`
6. **Logout**: Clear localStorage + API call

## 📊 Key Features

### Backend Features
- Custom email-based User model
- JWT authentication with auto-refresh
- Consistent API response format
- CORS configuration for frontend
- Health check endpoint
- Django admin interface

### Frontend Features
- Modular API service architecture
- TypeScript throughout
- Shadcn/UI component library
- Responsive design with Tailwind
- Authentication context
- Error handling utilities
- Auto token refresh
- SSR compatibility

## 🧪 Testing

### Integration Testing
- **File**: `test_integration.js`
- **Tests**: Health check, registration, login, protected endpoints
- **Command**: `node test_integration.js`

### Service Testing
Each service can be tested independently with proper TypeScript support.

## 🔧 Configuration

### Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `DJANGO_SECRET_KEY`: Django secret key
- `DJANGO_DEBUG`: Debug mode
- `DJANGO_ALLOWED_HOSTS`: Allowed hosts

### Development URLs
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Base: http://localhost:8000/api/v1

This structure provides a scalable, maintainable, and well-organized foundation for the Ovra AI Tax Assistant application.
