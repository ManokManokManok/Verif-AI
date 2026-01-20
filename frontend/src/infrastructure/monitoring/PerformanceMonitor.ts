/**
 * Performance Monitoring Service
 * Tracks application performance metrics and user experience
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

interface NavigationTiming {
  loadTime: number;
  domContentLoaded: number;
  firstPaint?: number;
  firstContentfulPaint?: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private isEnabled: boolean = true;

  constructor() {
    if (typeof window !== 'undefined') {
      this.setupPerformanceObserver();
      this.measureNavigationTiming();
    }
  }

  /**
   * Setup Performance Observer to track Web Vitals
   */
  private setupPerformanceObserver(): void {
    try {
      // Largest Contentful Paint (LCP)
      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        this.recordMetric('LCP', lastEntry.renderTime || lastEntry.loadTime);
      });
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });

      // First Input Delay (FID)
      const fidObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach((entry: any) => {
          this.recordMetric('FID', entry.processingStart - entry.startTime);
        });
      });
      fidObserver.observe({ type: 'first-input', buffered: true });

      // Cumulative Layout Shift (CLS)
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
            this.recordMetric('CLS', clsValue);
          }
        });
      });
      clsObserver.observe({ type: 'layout-shift', buffered: true });
    } catch (error) {
      console.warn('PerformanceObserver not supported:', error);
    }
  }

  /**
   * Measure navigation timing metrics
   */
  private measureNavigationTiming(): void {
    if (typeof window === 'undefined' || !window.performance) return;

    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        if (navigation) {
          const timing: NavigationTiming = {
            loadTime: navigation.loadEventEnd - navigation.fetchStart,
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
          };

          this.recordMetric('PageLoadTime', timing.loadTime);
          this.recordMetric('DOMContentLoaded', timing.domContentLoaded);
        }

        // First Paint and First Contentful Paint
        const paintEntries = performance.getEntriesByType('paint');
        paintEntries.forEach((entry) => {
          if (entry.name === 'first-paint') {
            this.recordMetric('FirstPaint', entry.startTime);
          } else if (entry.name === 'first-contentful-paint') {
            this.recordMetric('FirstContentfulPaint', entry.startTime);
          }
        });
      }, 0);
    });
  }

  /**
   * Record a performance metric
   */
  public recordMetric(name: string, value: number, metadata?: Record<string, any>): void {
    if (!this.isEnabled) return;

    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      metadata,
    };

    this.metrics.push(metric);

    // Log in development
    if (import.meta.env.DEV) {
      console.log(`[Performance] ${name}: ${value.toFixed(2)}ms`, metadata);
    }

    // Send to analytics service (implement as needed)
    this.sendToAnalytics(metric);
  }

  /**
   * Measure component render time
   */
  public measureRender(componentName: string, callback: () => void): void {
    const startTime = performance.now();
    callback();
    const endTime = performance.now();
    this.recordMetric(`Render_${componentName}`, endTime - startTime);
  }

  /**
   * Measure async operation time
   */
  public async measureAsync<T>(
    operationName: string,
    operation: () => Promise<T>
  ): Promise<T> {
    const startTime = performance.now();
    try {
      const result = await operation();
      const endTime = performance.now();
      this.recordMetric(operationName, endTime - startTime, { success: true });
      return result;
    } catch (error) {
      const endTime = performance.now();
      this.recordMetric(operationName, endTime - startTime, { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * Mark a custom timing point
   */
  public mark(name: string): void {
    if (typeof window !== 'undefined' && window.performance) {
      performance.mark(name);
    }
  }

  /**
   * Measure time between two marks
   */
  public measure(name: string, startMark: string, endMark: string): void {
    if (typeof window !== 'undefined' && window.performance) {
      try {
        performance.measure(name, startMark, endMark);
        const measure = performance.getEntriesByName(name, 'measure')[0];
        if (measure) {
          this.recordMetric(name, measure.duration);
        }
      } catch (error) {
        console.warn('Performance measurement failed:', error);
      }
    }
  }

  /**
   * Get all recorded metrics
   */
  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  /**
   * Get metrics by name
   */
  public getMetricsByName(name: string): PerformanceMetric[] {
    return this.metrics.filter(m => m.name === name);
  }

  /**
   * Get average value for a metric
   */
  public getAverageMetric(name: string): number | null {
    const metrics = this.getMetricsByName(name);
    if (metrics.length === 0) return null;
    
    const sum = metrics.reduce((acc, m) => acc + m.value, 0);
    return sum / metrics.length;
  }

  /**
   * Clear all metrics
   */
  public clearMetrics(): void {
    this.metrics = [];
  }

  /**
   * Enable/disable monitoring
   */
  public setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  /**
   * Send metrics to analytics service
   * Override this method to integrate with your analytics provider
   */
  private sendToAnalytics(_metric: PerformanceMetric): void {
    // Placeholder for analytics integration
    // Example: analytics.track('performance_metric', _metric);
  }

  /**
   * Get performance report
   */
  public getReport(): {
    webVitals: {
      lcp?: number;
      fid?: number;
      cls?: number;
    };
    timing: {
      pageLoadTime?: number;
      domContentLoaded?: number;
      firstPaint?: number;
      firstContentfulPaint?: number;
    };
    customMetrics: PerformanceMetric[];
  } {
    const lcpMetrics = this.getMetricsByName('LCP');
    const fidMetrics = this.getMetricsByName('FID');
    const clsMetrics = this.getMetricsByName('CLS');

    return {
      webVitals: {
        lcp: lcpMetrics.length > 0 ? lcpMetrics[lcpMetrics.length - 1].value : undefined,
        fid: fidMetrics.length > 0 ? fidMetrics[fidMetrics.length - 1].value : undefined,
        cls: clsMetrics.length > 0 ? clsMetrics[clsMetrics.length - 1].value : undefined,
      },
      timing: {
        pageLoadTime: this.getAverageMetric('PageLoadTime') ?? undefined,
        domContentLoaded: this.getAverageMetric('DOMContentLoaded') ?? undefined,
        firstPaint: this.getAverageMetric('FirstPaint') ?? undefined,
        firstContentfulPaint: this.getAverageMetric('FirstContentfulPaint') ?? undefined,
      },
      customMetrics: this.metrics.filter(m => 
        !['LCP', 'FID', 'CLS', 'PageLoadTime', 'DOMContentLoaded', 'FirstPaint', 'FirstContentfulPaint'].includes(m.name)
      ),
    };
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();
