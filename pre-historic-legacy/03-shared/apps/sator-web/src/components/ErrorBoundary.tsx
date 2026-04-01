import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    // Could send to error reporting service here
  }

  handleRefresh = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[50vh] flex items-center justify-center p-4">
          <div className="max-w-md w-full text-center">
            <div className="w-20 h-20 mx-auto mb-6 bg-radiant-red/10 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-10 h-10 text-radiant-red" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Something went wrong</h1>
            <p className="text-radiant-gray mb-6">
              We apologize for the inconvenience. An unexpected error has occurred.
            </p>
            {this.state.error && (
              <div className="mb-6 p-4 bg-radiant-card rounded-lg border border-radiant-border overflow-auto">
                <code className="text-sm text-radiant-red font-mono">
                  {this.state.error.message}
                </code>
              </div>
            )}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleRefresh}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-radiant-red hover:bg-radiant-red/90 text-white font-medium rounded-lg transition-all"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh Page
              </button>
              <Link
                to="/"
                onClick={this.handleReset}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-radiant-card hover:bg-radiant-border text-white font-medium rounded-lg border border-radiant-border transition-all"
              >
                <Home className="w-4 h-4" />
                Go Home
              </Link>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook for functional component error boundaries
import { useRouteError } from 'react-router-dom';

export function RouteErrorBoundary() {
  const error = useRouteError() as Error;

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="w-20 h-20 mx-auto mb-6 bg-radiant-red/10 rounded-full flex items-center justify-center">
          <AlertTriangle className="w-10 h-10 text-radiant-red" />
        </div>
        <h1 className="text-2xl font-bold mb-2">Page Error</h1>
        <p className="text-radiant-gray mb-6">
          There was an error loading this page.
        </p>
        {error?.message && (
          <div className="mb-6 p-4 bg-radiant-card rounded-lg border border-radiant-border">
            <code className="text-sm text-radiant-red font-mono">
              {error.message}
            </code>
          </div>
        )}
        <Link
          to="/"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-radiant-red hover:bg-radiant-red/90 text-white font-medium rounded-lg transition-all"
        >
          <Home className="w-4 h-4" />
          Go Home
        </Link>
      </div>
    </div>
  );
}
