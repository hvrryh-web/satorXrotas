/**
 * PRX-25-PATCH-03 — Cross-lane error boundary.
 *
 * Catches errors thrown by any descendant during render / lifecycle and
 * renders a friendly fallback with a recovery CTA. Errors are forwarded
 * to the `defaultEventBus` as `errorBoundary.caught` events so
 * observability tooling can pick them up (Sentry breadcrumb adapter,
 * analytics).
 *
 * Designed for module routes:
 *   <ErrorBoundary moduleSlug="focus-hero">
 *     <FocusRoute />
 *   </ErrorBoundary>
 *
 * Per-lane fallback copy + onRecover prop customisable.
 *
 * Important: this is the classic React class-component pattern. React 19
 * still requires class boundaries (there is no hook equivalent yet).
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { defaultEventBus } from '@njz-os/core';

export interface ErrorBoundaryProps {
  /** Used in telemetry + the default fallback copy. */
  moduleSlug: string;
  /** Friendly label shown in the default fallback ("Focus Hero", etc.). */
  moduleLabel?: string;
  /** Optional override for the fallback content. */
  fallback?: (state: {
    error: Error;
    moduleSlug: string;
    moduleLabel: string;
    recover: () => void;
  }) => ReactNode;
  /** Called when the user clicks the recover button (defaults to remount). */
  onRecover?: () => void;
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    defaultEventBus.emit('errorBoundary.caught', {
      moduleSlug: this.props.moduleSlug,
      err: { name: error.name, message: error.message, stack: error.stack, componentStack: info.componentStack ?? null },
    });
  }

  recover = (): void => {
    this.setState({ error: null });
    this.props.onRecover?.();
  };

  override render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    const moduleLabel = this.props.moduleLabel ?? this.props.moduleSlug;

    if (this.props.fallback) {
      return this.props.fallback({
        error,
        moduleSlug: this.props.moduleSlug,
        moduleLabel,
        recover: this.recover,
      });
    }

    return (
      <div role="alert" aria-live="polite" className="njz-error-boundary">
        <h2 className="njz-error-boundary__title">{moduleLabel} hit an unexpected error</h2>
        <p className="njz-error-boundary__body">
          The module crashed while rendering. Your session is preserved — try
          recovering, or head back to the home page.
        </p>
        <div className="njz-error-boundary__actions">
          <button
            type="button"
            onClick={this.recover}
            className="njz-error-boundary__btn njz-error-boundary__btn--primary"
          >
            Try again
          </button>
          <a
            href="/"
            className="njz-error-boundary__btn njz-error-boundary__btn--secondary"
          >
            Back to home
          </a>
        </div>
      </div>
    );
  }
}
