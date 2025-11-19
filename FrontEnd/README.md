# Application Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Next.js Frontend (Port 3000)                  │  │
│  │                                                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │ Auth Pages  │  │ Chat Page   │  │ Auth Context    │   │  │
│  │  │ - Login     │  │ - Messages  │  │ - User State    │   │  │
│  │  │ - Signup    │  │ - Input     │  │ - Auth Methods  │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │  │
│  │                                                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               │ Firebase SDK
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Firebase Services                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐         ┌──────────────────────┐      │
│  │  Authentication      │         │  Realtime Database   │      │
│  │                      │         │                      │      │
│  │  • Email/Password    │         │  users/              │      │
│  │  • Anonymous         │         │  ├─ {userId}/        │      │
│  │                      │         │  └─ anonymous/       │      │
│  │  Returns: User ID    │         │     └─ {userId}/     │      │
│  │                      │         │                      │      │
│  └──────────────────────┘         └──────────────────────┘      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Your Backend API (To Be Implemented)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐         ┌──────────────────────┐      │
│  │  RAG Pipeline        │         │  Vector Database     │      │
│  │                      │         │                      │      │
│  │  • Query Processing  │◄────────┤  • Document Storage  │      │
│  │  • Context Retrieval │         │  • Embeddings        │      │
│  │  • Response Gen.     │         │  • Similarity Search │      │
│  │                      │         │                      │      │
│  └──────────────────────┘         └──────────────────────┘      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Authentication Flow

```
┌─────────┐         ┌──────────┐         ┌──────────┐
│  User   │────────▶│  Login   │────────▶│ Firebase │
└─────────┘         │  Page    │         │   Auth   │
                    └──────────┘         └──────────┘
                         │                      │
                         │                      │
                         │        Auth Token    │
                         │◄─────────────────────┘
                         │
                         ▼
                    ┌──────────┐
                    │   Chat   │
                    │  Page    │
                    └──────────┘
```

#### Detailed Authentication Steps

1. **User Registration**
   ```
   User enters email/password
        ↓
   Frontend calls Firebase Auth (createUserWithEmailAndPassword)
        ↓
   Firebase creates user account
        ↓
   AuthContext receives user object
        ↓
   User data initialized in Realtime Database (users/{userId})
        ↓
   Redirect to /chat
   ```

2. **Guest Sign-in**
   ```
   User clicks "Continue as Guest"
        ↓
   Frontend calls Firebase Auth (signInAnonymously)
        ↓
   Firebase creates anonymous user
        ↓
   AuthContext receives anonymous user object
        ↓
   User data initialized in Realtime Database (users/anonymous/{userId})
        ↓
   Redirect to /chat
   ```

### Chat Message Flow

```
┌─────────┐         ┌──────────┐         ┌──────────┐
│  User   │────────▶│   Chat   │────────▶│ Firebase │
│  Types  │         │   Page   │         │ Realtime │
│ Message │         │          │         │ Database │
└─────────┘         └──────────┘         └──────────┘
                         │                      │
                         │    Message Saved     │
                         │◄─────────────────────┘
                         │
                         │
                         ▼
                    ┌──────────┐
                    │  Backend │
                    │   API    │
                    │  (RAG)   │
                    └──────────┘
                         │
                         │
                         ▼
                    ┌──────────┐
                    │   Chat   │◄──┐
                    │   Page   │   │
                    └──────────┘   │
                         │         │
                         │         │
                         ▼         │
                    ┌──────────┐  │
                    │ Firebase │──┘
                    │ Realtime │
                    │ Database │
                    └──────────┘
```

#### Detailed Message Steps

1. **User Sends Message**
   ```
   User types message and clicks Send
        ↓
   Frontend saves message to Firebase Realtime Database
   Path: users/{userId}/conversations/default/messages
   Data: { role: "user", content: "...", timestamp: ... }
        ↓
   Frontend calls backend API (TODO: implement)
        ↓
   Backend processes with RAG pipeline
        ↓
   Backend returns response
        ↓
   Frontend saves response to Firebase Realtime Database
   Path: users/{userId}/conversations/default/messages
   Data: { role: "assistant", content: "...", timestamp: ... }
        ↓
   Real-time listener updates UI automatically
   ```

## Component Hierarchy

```
App (layout.tsx)
│
├─ AuthProvider (AuthContext.tsx)
│  └─ Manages authentication state globally
│
├─ Home Page (page.tsx)
│  └─ Redirects based on auth state
│
├─ Auth Pages
│  ├─ Login (/auth/login/page.tsx)
│  │  ├─ Email/Password form
│  │  └─ Guest sign-in button
│  │
│  └─ Signup (/auth/signup/page.tsx)
│     └─ Registration form
│
└─ Chat Page (/chat/page.tsx)
   ├─ Header (User info, Logout)
   ├─ Message List
   │  ├─ User messages (blue, right-aligned)
   │  └─ Assistant messages (white, left-aligned)
   └─ Input Form
      ├─ Text input
      └─ Send button
```

## Firebase Database Schema

```json
{
  "users": {
    "{userId}": {
      "uid": "string",
      "email": "string",
      "isAnonymous": false,
      "createdAt": "ISO8601 timestamp",
      "conversations": {
        "default": {
          "messages": {
            "{messageId1}": {
              "role": "user",
              "content": "Hello!",
              "timestamp": 1234567890
            },
            "{messageId2}": {
              "role": "assistant",
              "content": "Hi! How can I help?",
              "timestamp": 1234567891
            }
          }
        }
      }
    },
    "anonymous": {
      "{anonymousUserId}": {
        "uid": "string",
        "email": "anonymous",
        "isAnonymous": true,
        "createdAt": "ISO8601 timestamp",
        "conversations": {
          "default": {
            "messages": {
              "{messageId1}": {
                "role": "user",
                "content": "Hi there!",
                "timestamp": 1234567892
              }
            }
          }
        }
      }
    }
  }
}
```

## Security Rules

```json
{
  "rules": {
    "users": {
      "$userId": {
        // Authenticated users can only access their own data
        ".read": "$userId === auth.uid",
        ".write": "$userId === auth.uid"
      },
      "anonymous": {
        "$userId": {
          // Anonymous users can only access their own data
          ".read": "$userId === auth.uid",
          ".write": "$userId === auth.uid"
        }
      }
    }
  }
}
```

## State Management

### AuthContext State

```typescript
{
  user: User | null,           // Current user object from Firebase
  loading: boolean,            // Auth initialization state
  signUp: (email, password) => Promise<void>,
  signIn: (email, password) => Promise<void>,
  signInAsGuest: () => Promise<void>,
  logout: () => Promise<void>
}
```

### Chat Page State

```typescript
{
  messages: Message[],         // Array of chat messages
  input: string,               // Current input text
  isSending: boolean          // Sending state
}

interface Message {
  id: string,
  role: "user" | "assistant",
  content: string,
  timestamp: number
}
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14 | React framework with App Router |
| **Language** | TypeScript | Type-safe development |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **Authentication** | Firebase Auth | User management |
| **Database** | Firebase Realtime DB | Real-time data sync |
| **State** | React Context | Global state management |
| **Backend** | To be implemented | RAG pipeline integration |

## Routing Structure

```
/                           → Home (redirects based on auth)
├── /auth
│   ├── /login             → Login page
│   └── /signup            → Signup page
└── /chat                  → Chat interface (protected)
```

## Protected Routes

Chat page (`/chat`) is protected:
- Redirects to `/auth/login` if user is not authenticated
- Accessible only after successful authentication

## Real-time Synchronization

Firebase Realtime Database provides automatic synchronization:
- Messages saved by one device instantly appear on all connected devices
- No polling required - uses WebSocket connections
- Offline support with automatic sync when reconnected

## Future Enhancements

1. **Multiple Conversations**: Support for multiple chat threads
2. **Message History**: Pagination for long conversations
3. **File Uploads**: Support for document/image uploads
4. **Rich Text**: Markdown rendering for formatted responses
5. **Typing Indicators**: Show when assistant is typing
6. **Message Streaming**: Stream responses token by token
7. **Voice Input**: Speech-to-text integration
8. **Export Chats**: Download conversation history
