# API Services - Modular Architecture

This directory contains the modular API service architecture for the Ovra AI Tax Assistant frontend application. Each service is responsible for a specific domain of functionality, making the codebase more maintainable, testable, and scalable.

## 📁 Service Structure

```
services/
├── base.service.ts      # Base service with common HTTP methods
├── auth.service.ts      # Authentication and token management
├── user.service.ts      # User profile and account management
├── chat.service.ts      # AI chat and conversation management
├── config.ts           # Service configuration and settings
├── examples.ts         # Usage examples and patterns
├── index.ts            # Central export point
└── README.md           # This documentation
```

## 🚀 Quick Start

### Import Services

```typescript
// Import individual services
import { authService, userService, chatService } from '@/lib/services'

// Or import everything
import * as services from '@/lib/services'

// Legacy compatibility
import { apiService } from '@/lib/api' // Same as authService
```

### Basic Usage

```typescript
// Authentication
const loginResponse = await authService.login({
  email: 'user@example.com',
  password: 'password123'
})

// User management
const profile = await userService.getProfile()
await userService.updateProfile({ full_name: 'New Name' })

// AI Chat
const chatResponse = await chatService.sendMessage({
  message: 'What is VAT in Spain?'
})
```

## 📋 Service Details

### BaseApiService

**Purpose**: Provides common HTTP methods and utilities for all services.

**Key Features**:
- HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Authentication header management
- Response handling and error processing
- Token management utilities
- Server-side rendering compatibility

### AuthService

**Purpose**: Handles user authentication, registration, and token management.

**Key Methods**:
- `login(credentials)` - User login
- `register(userData)` - User registration
- `logout()` - User logout
- `refreshToken()` - Refresh access token
- `verifyToken()` - Verify token validity
- `isAuthenticated()` - Check auth status
- `getCurrentUser()` - Get current user data
- `autoRefreshToken()` - Auto-refresh before expiry

**Token Management**:
- Automatic token storage in localStorage
- Auto-refresh when tokens are about to expire
- Secure token handling with SSR compatibility

### UserService

**Purpose**: Manages user profile, preferences, and account operations.

**Key Methods**:
- `getProfile()` - Get user profile
- `updateProfile(data)` - Update profile
- `uploadProfilePicture(file)` - Upload profile image
- `getUserStats()` - Get usage statistics
- `getPreferences()` - Get user preferences
- `updatePreferences(prefs)` - Update preferences
- `deleteAccount()` - Delete user account
- `exportUserData()` - GDPR data export

### ChatService

**Purpose**: Handles AI chat interactions, conversations, and legal queries.

**Key Methods**:
- `sendMessage(request)` - Send message to AI
- `startConversation(message)` - Start new conversation
- `continueConversation(id, message)` - Continue existing chat
- `getConversation(id)` - Get conversation history
- `getConversations()` - List all conversations
- `searchConversations(query)` - Search chat history
- `getSuggestedQuestions()` - Get AI suggestions
- `rateMessage(id, rating)` - Rate AI responses
- `exportConversation(id)` - Export chat as PDF/text

## ⚙️ Configuration

The services use a centralized configuration system:

```typescript
import { config, configUtils } from '@/lib/services/config'

// Check if feature is enabled
if (configUtils.isFeatureEnabled('REAL_TIME_CHAT')) {
  // Enable real-time features
}

// Get endpoint URL
const url = configUtils.getEndpointUrl('/auth/login/')
```

### Environment Configuration

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.ovra-ai.com/api/v1`
- **Test**: `http://localhost:8001/api/v1`

## 🔧 Error Handling

The services provide comprehensive error handling utilities:

```typescript
import { apiUtils } from '@/lib/services'

try {
  await authService.login(credentials)
} catch (error) {
  if (apiUtils.isAuthError(error)) {
    // Handle authentication errors
    redirectToLogin()
  } else if (apiUtils.isNetworkError(error)) {
    // Handle network errors
    showNetworkError()
  } else {
    // Handle other errors
    showError(apiUtils.formatError(error))
  }
}
```

### Retry with Backoff

```typescript
const result = await apiUtils.retryWithBackoff(
  () => chatService.sendMessage({ message: 'Hello' }),
  3, // max retries
  1000 // base delay in ms
)
```

## 🎣 React Integration

### Custom Hooks Examples

```typescript
// Authentication hook
function useAuth() {
  const [user, setUser] = useState(authService.getCurrentUser())
  
  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password })
    setUser(response.user)
    return response
  }
  
  return { user, login, logout: authService.logout }
}

// Chat hook
function useChat(conversationId?: string) {
  const [messages, setMessages] = useState([])
  
  const sendMessage = async (message: string) => {
    const response = await chatService.sendMessage({
      message,
      conversation_id: conversationId
    })
    setMessages(prev => [...prev, response.message])
    return response
  }
  
  return { messages, sendMessage }
}
```

## 🧪 Testing

Each service can be tested independently:

```typescript
import { authService } from '@/lib/services'

describe('AuthService', () => {
  it('should login successfully', async () => {
    const response = await authService.login({
      email: 'test@example.com',
      password: 'password123'
    })
    expect(response.user).toBeDefined()
    expect(response.tokens).toBeDefined()
  })
})
```

## 🔄 Migration from Legacy API

If you're migrating from the old `apiService`:

```typescript
// Old way
import { apiService } from '@/lib/api'
await apiService.login(credentials)

// New way (recommended)
import { authService } from '@/lib/services'
await authService.login(credentials)

// Legacy compatibility (still works)
import { apiService } from '@/lib/api' // Same as authService
await apiService.login(credentials)
```

## 🚀 Best Practices

1. **Use TypeScript**: All services are fully typed
2. **Handle Errors**: Always wrap service calls in try-catch
3. **Auto-refresh Tokens**: Use `autoRefreshToken()` for long-running apps
4. **Retry Failed Requests**: Use `apiUtils.retryWithBackoff()` for network issues
5. **Check Feature Flags**: Use `configUtils.isFeatureEnabled()` before using features
6. **Validate File Uploads**: Check file size and type before uploading

## 📚 Additional Resources

- See `examples.ts` for comprehensive usage examples
- Check `config.ts` for all configuration options
- Review individual service files for detailed method documentation
- Use TypeScript IntelliSense for auto-completion and type checking

## 🤝 Contributing

When adding new API endpoints:

1. Add the endpoint to the appropriate service
2. Update TypeScript interfaces
3. Add configuration in `config.ts`
4. Write usage examples in `examples.ts`
5. Update this README if needed
