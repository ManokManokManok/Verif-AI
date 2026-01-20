import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { performanceMonitor } from './infrastructure/monitoring'

// Start performance monitoring
performanceMonitor.mark('app-start');

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)

// Measure app initialization
performanceMonitor.mark('app-rendered');
performanceMonitor.measure('app-initialization', 'app-start', 'app-rendered');
