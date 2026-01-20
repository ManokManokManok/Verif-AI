/**
 * Analytics Service
 * Tracks user interactions and application events
 */

export interface AnalyticsEvent {
  name: string;
  properties?: Record<string, any>;
  timestamp?: number;
  userId?: string;
  sessionId?: string;
}

export interface UserProperties {
  userId: string;
  email?: string;
  roles?: string[];
  [key: string]: any;
}

class AnalyticsService {
  private isEnabled: boolean = true;
  private userId: string | null = null;
  private sessionId: string;
  private events: AnalyticsEvent[] = [];

  constructor() {
    this.sessionId = this.generateSessionId();
    this.setupPageViewTracking();
  }

  /**
   * Generate a unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Setup automatic page view tracking
   */
  private setupPageViewTracking(): void {
    if (typeof window === 'undefined') return;

    // Track initial page view
    this.trackPageView(window.location.pathname);

    // Track subsequent navigation
    let lastPath = window.location.pathname;
    const checkPathChange = () => {
      if (window.location.pathname !== lastPath) {
        lastPath = window.location.pathname;
        this.trackPageView(lastPath);
      }
    };

    // Check for path changes every 500ms (simple SPA navigation tracking)
    setInterval(checkPathChange, 500);
  }

  /**
   * Initialize analytics with user identification
   */
  public identify(userId: string, properties?: UserProperties): void {
    this.userId = userId;
    
    if (import.meta.env.DEV) {
      console.log('[Analytics] User identified:', userId, properties);
    }

    // Send to analytics provider
    this.sendEvent({
      name: 'user_identified',
      properties: {
        userId,
        ...properties,
      },
    });
  }

  /**
   * Track a custom event
   */
  public track(eventName: string, properties?: Record<string, any>): void {
    if (!this.isEnabled) return;

    const event: AnalyticsEvent = {
      name: eventName,
      properties,
      timestamp: Date.now(),
      userId: this.userId || undefined,
      sessionId: this.sessionId,
    };

    this.events.push(event);

    if (import.meta.env.DEV) {
      console.log('[Analytics] Event tracked:', event);
    }

    this.sendEvent(event);
  }

  /**
   * Track page view
   */
  public trackPageView(path: string, properties?: Record<string, any>): void {
    this.track('page_view', {
      path,
      title: document.title,
      referrer: document.referrer,
      ...properties,
    });
  }

  /**
   * Track user login
   */
  public trackLogin(method: 'email' | 'social' = 'email'): void {
    this.track('user_login', {
      method,
      timestamp: Date.now(),
    });
  }

  /**
   * Track user logout
   */
  public trackLogout(): void {
    this.track('user_logout', {
      timestamp: Date.now(),
    });
    this.userId = null;
  }

  /**
   * Track user registration
   */
  public trackRegistration(method: 'email' | 'social' = 'email'): void {
    this.track('user_registration', {
      method,
      timestamp: Date.now(),
    });
  }

  /**
   * Track button click
   */
  public trackClick(buttonName: string, location?: string): void {
    this.track('button_click', {
      buttonName,
      location,
    });
  }

  /**
   * Track form submission
   */
  public trackFormSubmit(formName: string, success: boolean): void {
    this.track('form_submit', {
      formName,
      success,
    });
  }

  /**
   * Track error
   */
  public trackError(error: Error, context?: Record<string, any>): void {
    this.track('error', {
      message: error.message,
      stack: error.stack,
      name: error.name,
      ...context,
    });
  }

  /**
   * Track search
   */
  public trackSearch(query: string, resultsCount?: number): void {
    this.track('search', {
      query,
      resultsCount,
    });
  }

  /**
   * Track feature usage
   */
  public trackFeatureUsage(featureName: string, action: string): void {
    this.track('feature_usage', {
      featureName,
      action,
    });
  }

  /**
   * Track API call
   */
  public trackApiCall(endpoint: string, method: string, status: number, duration: number): void {
    this.track('api_call', {
      endpoint,
      method,
      status,
      duration,
      success: status >= 200 && status < 300,
    });
  }

  /**
   * Get all tracked events
   */
  public getEvents(): AnalyticsEvent[] {
    return [...this.events];
  }

  /**
   * Clear all events
   */
  public clearEvents(): void {
    this.events = [];
  }

  /**
   * Enable/disable analytics
   */
  public setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  /**
   * Send event to analytics provider
   * Override this method to integrate with your analytics provider
   */
  private sendEvent(event: AnalyticsEvent): void {
    // Placeholder for analytics provider integration
    // Examples:
    // - Google Analytics: gtag('event', event.name, event.properties);
    // - Mixpanel: mixpanel.track(event.name, event.properties);
    // - Segment: analytics.track(event.name, event.properties);
    // - PostHog: posthog.capture(event.name, event.properties);
    
    // For now, just log in development
    if (import.meta.env.DEV) {
      console.log('[Analytics] Event sent:', event);
    }
  }

  /**
   * Get session information
   */
  public getSessionInfo(): { sessionId: string; userId: string | null } {
    return {
      sessionId: this.sessionId,
      userId: this.userId,
    };
  }

  /**
   * Set user properties
   */
  public setUserProperties(properties: Record<string, any>): void {
    if (!this.userId) {
      console.warn('[Analytics] Cannot set user properties without user ID');
      return;
    }

    this.track('user_properties_updated', properties);
  }

  /**
   * Track time spent on page/feature
   */
  private timeTrackers: Map<string, number> = new Map();

  public startTimer(timerName: string): void {
    this.timeTrackers.set(timerName, Date.now());
  }

  public endTimer(timerName: string, properties?: Record<string, any>): void {
    const startTime = this.timeTrackers.get(timerName);
    if (!startTime) {
      console.warn(`[Analytics] Timer "${timerName}" was not started`);
      return;
    }

    const duration = Date.now() - startTime;
    this.track('time_spent', {
      timerName,
      duration,
      ...properties,
    });

    this.timeTrackers.delete(timerName);
  }
}

// Export singleton instance
export const analytics = new AnalyticsService();
