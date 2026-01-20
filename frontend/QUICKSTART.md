# Quick Start Guide for Developers

## First Time Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Create environment file**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Or on Windows:
   copy .env.example .env
   
   # The .env file contains:
   # VITE_API_URL=http://localhost:8000/api
   # VITE_API_TIMEOUT=30000
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   Open http://localhost:5174

## Daily Development

### Running the app
```bash
npm run dev          # Start dev server
```

### Running tests
```bash
npm test             # Watch mode
npm run test:run     # Run once
npm run test:ui      # Interactive UI
npm run test:coverage # Coverage report
```

### Building
```bash
npm run build        # Production build
npm run preview      # Preview production build
```

## Project Structure

```
src/
├── domain/              # Business logic (entities, services)
├── use_cases/          # Application logic
├── infrastructure/     # External services (API, storage)
└── interfaces/         # UI layer (components, pages, routes)
    ├── components/     # Reusable UI components
    ├── pages/          # Page components
    └── routers/        # Routing configuration
```

## Common Tasks

### Adding a new page
1. Create page component in `src/interfaces/pages/`
2. Add route in `src/interfaces/routers/AppRouter.tsx`
3. Link to it from navigation or other pages

### Adding a new API endpoint
1. Add method to appropriate API class in `src/infrastructure/api/`
2. Create or update use case in `src/use_cases/`
3. Use the use case in your component

### Adding a new component
1. Create component in `src/interfaces/components/`
2. Export from `index.ts` in the same directory
3. Import and use where needed

### Writing tests
- Place test file next to source file with `.test.ts` or `.test.tsx` extension
- Run `npm test` to see your tests in watch mode

## Code Standards

- **TypeScript** - Use proper types, avoid `any`
- **Clean Architecture** - Keep layers separated
- **Testing** - Write tests for new features
- **Formatting** - Use consistent formatting (Prettier recommended)
- **Naming** - Use clear, descriptive names

## Useful Commands

```bash
# Development
npm run dev              # Start dev server on port 5174

# Testing
npm test                 # Run tests in watch mode
npm run test:run         # Run tests once
npm run test:ui          # Interactive test UI
npm run test:coverage    # Generate coverage report

# Building
npm run build            # Create production build
npm run preview          # Preview production build

# Linting
npm run lint             # Check for linting errors

# Type checking
npx tsc --noEmit        # Check TypeScript types
```

## Troubleshooting

**Port already in use?**
```bash
# Kill process on port 5174 (Windows)
netstat -ano | findstr :5174
taskkill /PID <pid> /F
```

**Modules not found?**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Tests failing?**
```bash
npm run test:run -- --clearCache
```

## Need Help?

- Check the main README.md for detailed documentation
- Ask your team members
- Check existing code for examples
- Review the project structure diagram above
