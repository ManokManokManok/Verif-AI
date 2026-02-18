# Admin Pages Modular Architecture

This document describes the modular structure of admin pages, including organization patterns, best practices, and migration guidelines.

## Directory Structure

```
frontend/src/pages/admin/
├── AdminDashboard.jsx          # Main admin container
├── AdminDashboard.css
├── WebsiteAnalytics/           # Analytics page (modularized)
│   ├── WebsiteAnalytics.jsx    # Main component
│   ├── index.js                # Barrel exports
│   ├── utils.js                # Page-specific utilities
│   └── components/
│       ├── BarChart.jsx
│       ├── DeviceBreakdown.jsx
│       ├── HourlyPattern.jsx
│       └── RecentVisits.jsx
├── UserManagement/             # User management page (modularized)
│   ├── UserManagement.jsx      # Main component
│   ├── UserManagement.css      # Page-specific styles
│   ├── index.js                # Barrel exports
│   ├── utils.js                # Page-specific utilities
│   ├── columns.jsx             # Table column definitions
│   └── components/
│       ├── PasswordResetModal.jsx
│       └── EditUserModal.jsx
├── shared/                     # Shared utilities and styles
│   ├── utils/
│   │   ├── dateTime.js         # Date/time formatting
│   │   ├── formatters.js       # String/number formatting
│   │   └── index.js            # Barrel exports
│   └── README.md
├── AnalysisStats.jsx           # (To be modularized)
├── BlockchainVerification.jsx  # (To be modularized)
├── ModelHealth.jsx             # (To be modularized)
└── UserStats.jsx               # (To be modularized)
```

## Modularization Pattern

### Page Structure

Each modularized page follows this structure:

```
PageName/
├── PageName.jsx        # Main page component
├── PageName.css        # Page-specific styles (optional)
├── index.js            # Barrel exports
├── utils.js            # Page-specific utilities
├── columns.jsx         # Table columns (if using DataTable)
└── components/         # Page-specific sub-components
    ├── Component1.jsx
    ├── Component2.jsx
    └── ...
```

### File Responsibilities

1. **Main Component (`PageName.jsx`)**
   - Page-level state management
   - Data fetching (via custom hooks)
   - Layout composition
   - Event handling
   - ~150-200 lines max

2. **Components Folder**
   - Self-contained sub-components
   - Each component in its own file
   - Props for configuration and callbacks
   - 50-100 lines each

3. **Utils File (`utils.js`)**
   - Re-exports from `shared/utils` for backward compatibility
   - Page-specific utility functions (if any)

4. **Columns File (`columns.jsx`)**
   - DataTable column definitions
   - Cell renderers
   - Keeps table logic separate from main component

5. **Barrel Export (`index.js`)**
   - Default export for the main component
   - Named exports for sub-components and utilities
   - Enables clean imports

## Best Practices

### Component Organization

✅ **DO:**
- Keep components focused on a single responsibility
- Extract sub-components when JSX exceeds 30-40 lines
- Use PropTypes for type validation
- Co-locate component-specific styles
- Create barrel exports for clean imports

❌ **DON'T:**
- Mix multiple concerns in one component
- Let components exceed 200 lines
- Use inline styles for complex styling
- Create deep nesting (max 2-3 levels)

### Utility Functions

✅ **DO:**
- Use shared utilities from `shared/utils` when possible
- Keep utility functions pure (no side effects)
- Document complex utility functions
- Re-export from local utils.js for convenience

❌ **DON'T:**
- Duplicate utility functions across pages
- Put business logic in utilities (use hooks instead)
- Create utilities with side effects

### CSS Organization

✅ **DO:**
- Use BEM naming: `.page-name__element--modifier`
- Leverage CSS variables from admin theme
- Keep page-specific styles in PageName.css
- Use shared styles from components/admin

❌ **DON'T:**
- Use inline `<style>` tags (use .css files)
- Create global styles that affect other pages
- Duplicate style definitions

## Import Patterns

### From Admin Components

```javascript
import { 
  StatCard,
  DataTable,
  LoadingSpinner,
  ErrorMessage 
} from '../../components/admin';
```

### From Shared Utilities

```javascript
import { 
  formatTimeAgo,
  formatRole,
  formatBytes 
} from '../shared/utils';
```

### From Page Modules (External)

```javascript
// Import main component
import WebsiteAnalytics from './WebsiteAnalytics';

// Or import sub-components
import { BarChart, DeviceBreakdown } from './WebsiteAnalytics';
```

### Within Page Module (Internal)

```javascript
// In WebsiteAnalytics.jsx
import BarChart from './components/BarChart';
import DeviceBreakdown from './components/DeviceBreakdown';
import { formatTimeAgo } from './utils';
```

## Migration Guide

### When to Modularize a Page

Consider modularizing when:
- Page exceeds 300 lines
- Contains 3+ internal components
- Has complex modal/form logic
- Shares utilities with other pages
- Difficult to navigate/maintain

### Step-by-Step Migration

1. **Create Module Folder**
   ```
   mkdir frontend/src/pages/admin/PageName
   ```

2. **Identify Sub-Components**
   - Look for repeated JSX patterns
   - Find internal component functions
   - Identify modal/form components

3. **Extract Components**
   - Create `components/` folder
   - Move each sub-component to own file
   - Add PropTypes validation
   - Import in main component

4. **Extract Utilities**
   - Check if utility exists in `shared/utils`
   - If shared, use from `shared/utils`
   - If page-specific, keep in local `utils.js`
   - Re-export from local utils for convenience

5. **Move Styles**
   - Extract inline `<style>` to `.css` file
   - Use BEM naming convention
   - Reference CSS variables

6. **Create Barrel Export**
   - Create `index.js` with exports
   - Export default and named exports
   - Update imports in AdminDashboard

7. **Test Thoroughly**
   - Check for import errors
   - Verify all functionality works
   - Test responsive behavior
   - Validate form submissions

## Examples

### WebsiteAnalytics Module

**Before:** 348 lines in one file  
**After:** ~100 line main component + 4 sub-components

Extracted:
- BarChart (generic bar chart)
- DeviceBreakdown (device statistics)
- HourlyPattern (24-hour traffic)
- RecentVisits (live visit feed)

### UserManagement Module

**Before:** 622 lines in one file  
**After:** ~270 line main component + modular structure

Extracted:
- PasswordResetModal (password reset form)
- EditUserModal (user edit form)
- getUserTableColumns (table configuration)
- Shared utilities (formatRole, formatRelativeTime)

## Backward Compatibility

All modularized pages maintain backward compatibility through barrel exports:

```javascript
// Old import (still works)
import WebsiteAnalytics from './WebsiteAnalytics';

// New import (same result)
import WebsiteAnalytics from './WebsiteAnalytics/WebsiteAnalytics';
import WebsiteAnalytics from './WebsiteAnalytics/index';
```

## Performance Considerations

- Use `React.memo()` for expensive components
- Leverage `useMemo()` and `useCallback()` for optimizations
- Code-split large pages with `React.lazy()`
- Keep bundle sizes reasonable (< 50KB per page)

## Testing

Each modularized page should have:
- Component tests (AdminComponents.test.jsx)
- Integration tests (AdminE2E.test.jsx)
- Hook tests (useAdminData.test.js)

Example test structure:
```javascript
describe('WebsiteAnalytics', () => {
  it('renders loading state', () => { ... });
  it('displays analytics data', () => { ... });
  it('handles errors gracefully', () => { ... });
});
```

## Future Improvements

- [ ] Modularize remaining pages (AnalysisStats, BlockchainVerification, etc.)
- [ ] Create shared form components
- [ ] Add Storybook documentation
- [ ] Implement lazy loading for modals
- [ ] Create shared TypeScript types

## Questions?

For questions or suggestions about the modular architecture, refer to:
- `/frontend/src/components/admin/README.md` - Component library docs
- `/frontend/src/pages/admin/shared/README.md` - Shared utilities docs
