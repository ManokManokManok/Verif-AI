import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from '../ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI
 */
export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // You can also log the error to an error reporting service here
    // Example: logErrorToService(error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      // Custom fallback UI provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
            <div className="flex flex-col items-center text-center">
              {/* Error Icon */}
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <AlertTriangle className="h-8 w-8 text-red-600" />
              </div>

              {/* Error Title */}
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Oops! Something went wrong
              </h1>

              {/* Error Description */}
              <p className="text-gray-600 mb-6">
                We encountered an unexpected error. Don't worry, our team has been notified.
              </p>

              {/* Error Details (Development Mode) */}
              {import.meta.env.DEV && this.state.error && (
                <div className="w-full mb-6 p-4 bg-gray-100 rounded-lg text-left">
                  <p className="text-sm font-semibold text-gray-900 mb-2">
                    Error Details:
                  </p>
                  <p className="text-xs text-red-600 font-mono mb-2">
                    {this.state.error.toString()}
                  </p>
                  {this.state.errorInfo && (
                    <details className="mt-2">
                      <summary className="text-xs font-medium text-gray-700 cursor-pointer">
                        Stack Trace
                      </summary>
                      <pre className="mt-2 text-xs text-gray-600 overflow-auto max-h-40">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 w-full">
                <Button
                  onClick={this.handleReset}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700"
                >
                  <RefreshCw size={16} className="mr-2" />
                  Try Again
                </Button>
                <Button
                  onClick={this.handleGoHome}
                  variant="outline"
                  className="flex-1"
                >
                  <Home size={16} className="mr-2" />
                  Go Home
                </Button>
              </div>

              {/* Help Text */}
              <p className="text-xs text-gray-500 mt-6">
                If this problem persists, please contact support at{' '}
                <a href="mailto:support@verifai.com" className="text-indigo-600 hover:underline">
                  support@verifai.com
                </a>
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
