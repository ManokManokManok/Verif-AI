# Verif-AI Frontend

Modern React-based frontend for the Verif-AI scam detection platform. Features AI-powered scam detection, real-time analytics, and comprehensive admin management tools.

## 🚀 Tech Stack

- **Framework**: React 18.3.1
- **Build Tool**: Vite 5.4.8
- **Routing**: React Router DOM 6.28.0
- **Styling**: Plain CSS with CSS Variables (Dark theme)
- **Testing**: Vitest + React Testing Library
- **Type Checking**: PropTypes

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/                    # API client and endpoints
│   │   ├── client.js           # Core API client with auth
│   │   ├── detection.js        # Scam detection endpoints
│   │   ├── admin.js            # Admin management endpoints
│   │   └── analytics.js        # Analytics endpoints
│   │
│   ├── components/             # Reusable components
│   │   ├── admin/              # Admin-specific components
│   │   │   ├── data/           # Data display components (StatCard, MetricGauge, etc.)
│   │   │   ├── feedback/       # Feedback components (Alert, LoadingSpinner, etc.)
│   │   │   ├── forms/          # Form components (FormField, SearchBar, etc.)
│   │   │   ├── layout/         # Layout components (AdminSidebar)
│   │   │   ├── modals/         # Modal components (ConfirmModal, UserModal, etc.)
│   │   │   └── tables/         # Table components (DataTable, Pagination, etc.)
│   │   ├── auth/               # Auth-specific components (SessionExpiredModal)
│   │   ├── reports/            # Report-related components
│   │   └── ChatBot.jsx         # AI chatbot component
│   │
│   ├── context/                # React Context providers
│   │   └── AuthContext.jsx     # Authentication state management
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAdminData.js     # Admin data fetching hooks
│   │   ├── useNotification.js  # Notification management
│   │   └── useWebSocket.js     # WebSocket connections
│   │
│   ├── pages/                  # Page components (routes)
│   │   ├── admin/              # Admin pages (modular structure)
│   │   │   ├── AdminDashboard/ # Main admin container
│   │   │   ├── AnalysisStats/  # Analysis statistics & trends
│   │   │   ├── ModelHealth/    # System health monitoring
│   │   │   ├── UserManagement/ # User CRUD operations
│   │   │   ├── UserStats/      # User analytics & reports
│   │   │   ├── WebsiteAnalytics/ # Website traffic analytics
│   │   │   ├── shared/         # Shared utilities & components
│   │   │   └── index.js        # Barrel exports
│   │   ├── AIChatbot.jsx       # AI chatbot page
│   │   ├── Detection.jsx       # Scam detection page
│   │   ├── ForgotPassword.jsx  # Password recovery
│   │   ├── Landing.jsx         # Home/landing page
│   │   ├── Login.jsx           # Login page
│   │   ├── ResetPassword.jsx   # Password reset
│   │   ├── Signup.jsx          # Registration page
│   │   └── VerifyEmail.jsx     # Email verification
│   │
│   ├── utils/                  # Utility functions
│   │   ├── formatters.js       # Data formatting utilities
│   │   └── validators.js       # Input validation
│   │
│   ├── App.jsx                 # Main app component with routing
│   ├── main.jsx                # App entry point
│   └── index.css               # Global styles & CSS variables
│
├── tests/                      # Test files
├── coverage/                   # Test coverage reports
├── package.json                # Dependencies & scripts
└── vite.config.js              # Vite configuration

```

## 🎨 Features & Pages

### Public Pages
- Call-to-action buttons
- Responsive design
- Detailed scam analysis reports
- Export reports as PDF/JSON
- Real-time typing indicators
- Markdown support for responses
- **Forgot Password** (`/forgot-password`): Password recovery flow
- **Reset Password** (`/reset-password`): New password setup

### Admin Pages (`/admin`)

Comprehensive admin dashboard with 6 modular sections:
- Mobile-responsive layout
- Role-based access control
- 30-second auto-refresh
- Uptime tracking
- `SystemGaugeCard`: Metric gauge with details
- `SystemInfoCard`: System information grid
- Scam type analytics
- Growth trends & percentages
- `RiskBreakdownCard`: Risk level progress bars
- `DailyActivityChart`: Activity visualization
- Registration trends
- Report filtering (All/Active/Inactive)
**Components:**
- `RoleDistributionCard`: Role breakdown display
- Pagination
- Bulk operations
- `RoleManagementModal`: Role assignment
- `UserStatsModal`: Individual user statistics
- Recent visits log
- Geographic analytics (if enabled)
- `HourlyPattern`: 24-hour activity chart
- `RecentVisits`: Real-time visit log
- Force re-anchor capability
- Transaction hash display
Located in `src/components/admin/`, organized by category:

#### Data Display
- **StatCard**: Metric card with optional trend indicator
- **MetricGauge**: Circular/linear gauge for system metrics
- **DataTable**: Generic table with sorting, filtering, actions
- **EmptyState**: Placeholder for no data scenarios

#### Forms
- **FormField**: Reusable form input with validation
- **SearchBar**: Search input with debouncing
- **Select**: Custom dropdown component
- **Toggle**: Switch/toggle button

#### Feedback
- **Alert**: Notification banner (success, error, warning, info)
- **LoadingSpinner**: Loading indicator (small, medium, large)
- **ErrorMessage**: Error display with retry option
- **ConfirmModal**: Confirmation dialog

#### Layout
- **AdminSidebar**: Collapsible navigation sidebar
- **PageHeader**: Consistent page headers
- **Card**: Generic card container

#### Tables
- **Pagination**: Page navigation controls
- **SortableHeader**: Table header with sorting
- **ActionMenu**: Dropdown action menu for rows
  - `formatRole()`: Format user roles
  - `formatDate()`: Date formatting
  - `formatNumber()`: Number formatting with locale

- **validators.js**: Input validation
  - `validateEmail()`: Email format validation
  - `validatePassword()`: Password strength checks
  - `validateUsername()`: Username rules

## 🔌 API Integration

### API Client (`src/api/client.js`)

Centralized HTTP client with:
- Authentication token management
- Automatic token refresh
- Error handling
- CSRF protection
- Session management

**Key Features:**
```javascript
// Automatic auth headers
apiClient.get('/endpoint'); // Includes Authorization header

// Token refresh on 401
// Automatic logout on token expiry
// Local storage synchronization
```

### API Modules

- **detection.js**: Scam detection analysis
  - `analyzeContent()`: Submit detection request
  - `getAnalysis()`: Fetch analysis results
  - `getAnalysisHistory()`: User analysis history

- **admin.js**: Admin operations
  - `getUsers()`: List users with pagination
  - `createUser()`: Create new user
  - `updateUser()`: Update user details
  - `deleteUser()`: Remove user
  - `updateUserRole()`: Change user permissions

- **analytics.js**: Analytics data
  - `getWebsiteAnalytics()`: Traffic data
  - `getAnalysisStats()`: Detection statistics
  - `getUserStats()`: User metrics
  - `getModelHealth()`: System health

## 🎯 State Management

### AuthContext

Global authentication state using React Context:

**Provided State:**
- `user`: Current user object
- `isLoggedIn`: Authentication status
- `isAdmin`: Admin role check
- `loading`: Auth loading state
- `error`: Auth error messages
- `sessionExpired`: Session expiration flag

**Provided Methods:**
- `login(email, password)`: Authenticate user
- `logout()`: Clear session
- `refreshUser()`: Sync user state
- `hasRole(role)`: Check user role

**Usage:**
```javascript
import { useAuth } from './context/AuthContext';

function Component() {
  const { user, isLoggedIn, login, logout } = useAuth();
  // ...
}
```

### Custom Hooks

#### useAdminData.js
- `useModelHealth(interval)`: System metrics with polling
- `useAnalysisStats()`: Analysis statistics
- `useUserStats()`: User statistics
- `useUserReports()`: User activity reports

#### useNotification.js
- Toast notification management
- Auto-dismiss timers
- Multiple notification types

#### useWebSocket.js
- Real-time data connections
- Automatic reconnection
- Event handling

## 🎨 Styling Architecture

### CSS Organization

- **index.css**: Global styles, CSS variables, reset
- **Component CSS**: Co-located with components
- **Page CSS**: Co-located with page modules
- **BEM Naming**: Block-Element-Modifier convention

### CSS Variables (Dark Theme)

```css
/* Colors */
--admin-bg-dark: #050b16
--admin-bg-card: #1f2937
--admin-border: #374151
--admin-text: #f9fafb
--admin-text-muted: #9ca3af
--admin-primary: #3b82f6
--admin-success: #22c55e
--admin-warning: #f59e0b
--admin-danger: #ef4444

/* Spacing */
--spacing-xs: 0.25rem
--spacing-sm: 0.5rem
--spacing-md: 1rem
--spacing-lg: 1.5rem
--spacing-xl: 2rem

/* Border Radius */
--radius-sm: 4px
--radius-md: 8px
--radius-lg: 12px
```

### Responsive Design

- Mobile-first approach
- Breakpoints: 768px (tablet), 1024px (desktop)
- Flexible layouts with CSS Grid & Flexbox
- Touch-friendly UI elements

## 🔐 Authentication & Authorization

### Protected Routes

```javascript
<ProtectedRoute requireAdmin={true}>
  <AdminDashboard />
</ProtectedRoute>
```

### Role-Based Access Control

- **Public**: Landing, Login, Signup, Detection, Chatbot
- **Authenticated**: Detection history, Profile
- **Admin**: Full admin dashboard access

### Session Management

- JWT token-based authentication
- Automatic token refresh
- Session expiration handling
- Secure token storage (httpOnly cookies)
- Session expired modal with re-login

## 📊 Recent Modularization (Feb 2026)

### Refactored Admin Pages

All admin pages refactored into modular folder structure:

**Before:** Monolithic 300-600 line files
**After:** ~50% reduction, reusable components

| Page | Before | After | Reduction |
|------|--------|-------|-----------|
| WebsiteAnalytics | 348 lines | ~100 lines | 71% |
| UserManagement | 622 lines | ~270 lines | 57% |
| ModelHealth | 406 lines | ~200 lines | 51% |
| AnalysisStats | 425 lines | ~200 lines | 53% |
| UserStats | 440 lines | ~250 lines | 43% |
| AdminDashboard | 127 lines | ~127 lines | Organized |

**Total:** ~1,792 lines → ~870 lines (51% reduction)

### Modular Architecture Benefits

✅ **Reusability**: Components extracted for multi-page use
✅ **Maintainability**: Smaller, focused files
✅ **Testability**: Isolated component testing
✅ **Collaboration**: Reduced merge conflicts
✅ **Performance**: Better code splitting
✅ **Consistency**: Shared component library

### Barrel Exports

Each module exports via `index.js`:
```javascript
// pages/admin/ModelHealth/index.js
export { default } from './ModelHealth';
export { default as SystemGaugeCard } from './components/SystemGaugeCard';
export { default as SystemInfoCard } from './components/SystemInfoCard';
export * from './utils';
```

**Backward Compatible:** Existing imports continue to work!

## 🧪 Testing

### Test Configuration

- **Framework**: Vitest
- **Utilities**: React Testing Library
- **DOM**: jsdom
- **Coverage**: Code coverage reports

### Running Tests

```bash
# Run tests in watch mode
npm run test

# Run tests once
npm run test:run

# Generate coverage report
npm run test:coverage
```

### Test Coverage

Coverage reports available in `coverage/` directory with:
- Line coverage
- Branch coverage
- Function coverage
- Statement coverage

### Test Files

Located in `tests/`:
- `AdminComponents.test.jsx`: Admin components
- `AdminE2E.test.jsx`: End-to-end admin flows
- `analytics.test.js`: Analytics functionality
- `useAdminData.test.js`: Custom hooks
- `WebsiteAnalytics.test.jsx`: Analytics page

## 🚀 Development

### Setup

```bash
# Install dependencies
npm install

# Start development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create `.env` file in root:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### Development Server

- **URL**: http://localhost:5173
- **Hot Reload**: Automatic on file changes
- **Port**: Configurable in `vite.config.js`

### Build Output

```bash
npm run build
# Output: dist/ directory
# Optimized, minified, code-split bundles
```

## 📝 Code Conventions

### JavaScript/React

- **ES6+**: Modern JavaScript features
- **Functional Components**: React Hooks over class components
- **PropTypes**: Type checking for components
- **JSDoc**: Component/function documentation
- **Const**: Prefer const over let/var

### File Naming

- **Components**: PascalCase (`UserModal.jsx`)
- **Utilities**: camelCase (`formatters.js`)
- **CSS**: Match component name (`UserModal.css`)
- **Tests**: `*.test.jsx` or `*.test.js`

### Component Structure

```jsx
/**
 * Component Description
 * 
 * Usage notes and examples.
 */
import React from 'react';
import PropTypes from 'prop-types';
import './Component.css';

export default function Component({ prop1, prop2 }) {
  // Hooks
  // Event handlers
  // Render logic
  
  return (
    <div className="component">
      {/* JSX */}
    </div>
  );
}

Component.propTypes = {
  prop1: PropTypes.string.isRequired,
  prop2: PropTypes.number,
};
```

### Import Order

1. React & external libraries
2. Context & hooks
3. Components
4. Utilities
5. Styles

## 🔍 Key Features Implementation

### 1. Real-time Detection

- WebSocket connection for live updates
- Progress indicators during analysis
- Streaming AI responses
- Auto-save analysis history

### 2. Admin Analytics

- Real-time metrics with auto-refresh
- Interactive charts & visualizations
- Data export capabilities
- Historical trend analysis

### 4. User Management

- Complete CRUD operations
- Role-based permissions
- Bulk user operations
- Activity audit trails

### 5. Responsive Design

- Mobile-first CSS
- Touch-optimized interactions
- Adaptive layouts
- Progressive enhancement

## 🐛 Error Handling

### Global Error Boundaries

```javascript
// Catch React component errors
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

### API Error Handling

```javascript
try {
  const data = await apiCall();
} catch (error) {
  if (error.status === 401) {
    // Auto-logout
  }
  if (error.status === 403) {
    // Permission denied
  }
  // Show error notification
}
```

### Form Validation

- Client-side validation before submission
- Server-side validation error display
- Field-level error messages
- Accessibility (ARIA labels)

## 📚 Additional Resources

- **Admin Components Docs**: `src/components/admin/README.md`
- **Modularization Summary**: `src/pages/admin/MODULARIZATION_SUMMARY.md`
- **API Reference**: `../backend/docs/API_REFERENCE.md`
- **Vite Docs**: https://vitejs.dev
- **React Router**: https://reactrouter.com

## 🤝 Contributing

1. Follow existing code structure and conventions
2. Write tests for new features
3. Update documentation
4. Use meaningful commit messages
5. Ensure no linting/build errors

## 📄 License

Private - Verif-AI Platform © 2026

---

**Last Updated:** February 18, 2026  
**Frontend Version:** 0.0.1  
**Node Version:** 20.x+  
**React Version:** 18.3.1
