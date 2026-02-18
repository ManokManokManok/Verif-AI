# Admin Pages - Shared Utilities

Common utility functions used across admin pages.

## Date & Time Utilities

Located in `utils/dateTime.js`:

- `formatTimeAgo(timestamp)` - Format as "5m ago", "2h ago", etc.
- `formatRelativeTime(dateString)` - Format with more detail (days, hours, etc.)
- `formatDate(dateString, options)` - Format as localized date
- `formatDateTime(dateString)` - Format as localized date and time

## String Formatters

Located in `utils/formatters.js`:

- `formatRole(role)` - Convert "premium_user" to "Premium User"
- `truncate(text, maxLength)` - Truncate text with ellipsis
- `formatBytes(bytes, decimals)` - Format bytes as "1.5 MB"
- `formatNumber(num, decimals)` - Format with locale-specific separators
- `formatPercentage(value, total, decimals)` - Calculate and format percentage

## Usage

```javascript
import { formatTimeAgo, formatRole, formatBytes } from '../shared/utils';

// Use in your components
const timeAgo = formatTimeAgo(timestamp);
const roleName = formatRole('premium_user'); // "Premium User"
const size = formatBytes(1024000); // "1 MB"
```

## Guidelines

- These utilities are shared across all admin pages
- Keep functions pure (no side effects)
- Add tests for new utility functions
- Document parameters and return values
