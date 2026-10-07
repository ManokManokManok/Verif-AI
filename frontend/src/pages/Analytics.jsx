import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Analytics.css';
import { useAuth } from '../context/AuthContext';
import AppNavLinks from '../components/AppNavLinks';
import { getUserSafetySummary, getGlobalSafetySummary, getUserAiSummary, getUserAiSummaryCached } from '../api/analytics';

const ANALYTICS_CACHE_TTL_MS = 60 * 1000;
let analyticsCache = null;

const ActivityRecharts = lazy(() => import('./ActivityRecharts.jsx'));
const CommunityLineChart = lazy(() => import('./ActivityRecharts.jsx').then((module) => ({ default: module.CommunityLineChart })));

function BarChart({ items, emptyText, horizontal = false }) {
  if (!items.length) return <p className="journey__empty">{emptyText}</p>;

  const maxCount = Math.max(...items.map((item) => item.count), 1);
  return (
    <div className={`journey__bar-graph ${horizontal ? 'journey__bar-graph--horizontal' : ''}`} aria-label="Scam types chart">
      {items.map((item) => (
        <div className="journey__bar-graph-item" key={item.type}>
          <div className="journey__bar-graph-label"><span title={item.type}>{item.type}</span><b>{item.count}</b></div>
          <div className="journey__bar-graph-track">
            <span style={horizontal
              ? { width: `${Math.max((item.count / maxCount) * 100, 10)}%`, flex: `0 0 ${Math.max((item.count / maxCount) * 100, 10)}%` }
              : { height: `${Math.max((item.count / maxCount) * 100, 16)}%` }} />
          </div>
          {!horizontal && <div className="journey__bar-graph-name" title={item.type}>{item.type}</div>}
        </div>
      ))}
    </div>
  );
}

function TrendChart({ points, emptyText }) {
  if (!points.length) return <p className="journey__empty">{emptyText}</p>;

  const maxCount = Math.max(...points.map((point) => point.count), 1);
  return (
    <div className="journey__trend-chart" aria-label="Monthly activity chart">
      {points.map((point) => (
        <div className="journey__trend-column" key={point.label}>
          <div className="journey__trend-value">{point.count}</div>
          <div className="journey__trend-track">
            <span style={{ '--bar-height': `${Math.max((point.count / maxCount) * 100, 8)}%` }} />
          </div>
          <span className="journey__trend-label">{point.label}</span>
        </div>
      ))}
    </div>
  );
}

function ActivityEmptyState({ onAnalyze, message = 'Your activity map will appear after your first check.' }) {
  return (
    <div className="journey__activity-empty">
      <p>{message}</p>
      <button type="button" onClick={onAnalyze}>Analyze a message <span aria-hidden="true">→</span></button>
    </div>
  );
}

function ActivityStatusRow({ activity, personal }) {
  const recent = activity?.recent_30_days || {};
  const previous = activity?.previous_30_days || {};
  const recentRate = recent.high_risk_rate ?? personal?.high_risk_rate ?? 0;
  const rateChange = recentRate - (previous.high_risk_rate ?? 0);
  const earlySignal = (recent.total_checks ?? 0) < 5 || (previous.total_checks ?? 0) < 5;
  const verdict = earlySignal ? 'Early signal' : rateChange <= -5 ? 'Improving' : rateChange >= 5 ? 'Rising' : 'Steady';
  const direction = rateChange < 0 ? 'down' : rateChange > 0 ? 'up' : 'unchanged';
  const daysSinceHighRisk = activity?.days_since_last_high_risk;
  const daysLabel = daysSinceHighRisk === 0 ? 'Today' : daysSinceHighRisk === 1 ? '1 day ago' : `${daysSinceHighRisk} days ago`;

  return (
    <div className="journey__activity-kpis" aria-label="Recent activity status">
      <article className="journey__activity-kpi journey__activity-kpi--rate">
        <span className="journey__activity-kpi-label">High-risk rate</span>
        <strong>{recentRate}<small>%</small></strong>
        <span className={`journey__activity-delta journey__activity-delta--${direction}`}>
          {earlySignal
            ? `Early signal · ${recent.total_checks ?? 0} checks in the last 30 days`
            : `${Math.abs(rateChange).toFixed(1)} percentage points ${direction} vs previous 30 days`}
        </span>
      </article>
      <article className={`journey__activity-kpi journey__activity-kpi--${verdict.toLowerCase().replace(' ', '-')}`}>
        <span className="journey__activity-kpi-label">Trend verdict</span>
        <strong>{verdict}</strong>
        <span className="journey__activity-kpi-copy">{personal?.activity_insight || 'Keep checking messages to see how your risk pattern changes over time.'}</span>
      </article>
      <article className="journey__activity-kpi journey__activity-kpi--last-risk">
        <span className="journey__activity-kpi-label">Since your last high-risk result</span>
        {daysSinceHighRisk == null ? (
          <><strong>Checks this month</strong><span className="journey__activity-kpi-copy">{activity?.checks_this_month ?? personal?.total_checks ?? 0} checks so far</span></>
        ) : (
          <><strong>{daysLabel}</strong><span className="journey__activity-kpi-copy">Last high-risk result</span></>
        )}
      </article>
    </div>
  );
}

function ActivityRiskMix({ activity, totalChecks, onAnalyze }) {
  const riskMix = activity?.risk_mix || { not_scam: 0, suspicious: 0, high_risk: 0 };
  const segments = [
    { key: 'not_scam', label: 'Not scam', color: 'safe' },
    { key: 'suspicious', label: 'Suspicious', color: 'review' },
    { key: 'high_risk', label: 'High risk', color: 'high' },
  ];
  const total = segments.reduce((sum, segment) => sum + (riskMix[segment.key] || 0), 0);

  return (
    <section className="journey__risk-mix" aria-labelledby="activity-risk-mix-title">
      <div className="journey__risk-mix-heading">
        <div><p className="journey__eyebrow">Your risk mix</p><h3 id="activity-risk-mix-title">What your checks found</h3></div>
        <span>{totalChecks} total checks</span>
      </div>
      {total === 0 ? <ActivityEmptyState onAnalyze={onAnalyze} message="Your risk mix will appear after your first check." /> : (
        <>
          <div className="journey__risk-mix-bar" role="img" aria-label={segments.map((segment) => `${segment.label}: ${riskMix[segment.key] || 0} checks`).join(', ')}>
            {segments.map((segment) => (
              <span
                key={segment.key}
                className={`journey__risk-mix-segment journey__risk-mix-segment--${segment.color}`}
                style={{ width: `${((riskMix[segment.key] || 0) / total) * 100}%` }}
              />
            ))}
          </div>
          <div className="journey__risk-mix-legend">
            {segments.map((segment) => (
              <span key={segment.key}>
                <i className={`journey__risk-mix-swatch journey__risk-mix-swatch--${segment.color}`} aria-hidden="true" />
                <strong>{riskMix[segment.key] || 0}</strong> {segment.label}
              </span>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function ActivityChartPanel({ activity, activeView, setActiveView, selectedDay, setSelectedDay, totalChecks, onAnalyze }) {
  const monthly = activity?.monthly_risk || [];
  const calendarDays = activity?.calendar_days || [];
  const weekdays = activity?.weekday_activity || [];
  const calendarTotal = calendarDays.reduce((sum, day) => sum + day.count, 0);
  const weekdayTotal = weekdays.reduce((sum, day) => sum + day.total_count, 0);
  const recent = activity?.recent_30_days || {};
  const previous = activity?.previous_30_days || {};
  const smallMonthlySample = (recent.total_checks ?? 0) < 5 || (previous.total_checks ?? 0) < 5;
  const maxDayCount = Math.max(...calendarDays.map((day) => day.count), 1);
  const weekdayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const busiestDay = calendarDays.reduce((best, day) => day.count > (best?.count || 0) ? day : best, null);
  const busiestWeekday = weekdays.reduce((best, day) => day.scam_count > (best?.scam_count || 0) ? day : best, null);

  let insight = 'Checks across each active month are split by risk level.';
  if (activeView === 'monthly') {
    insight = smallMonthlySample
      ? 'Early signal: make a few more checks before reading too much into a 30-day change.'
      : `High-risk checks ${recent.high_risk_count < previous.high_risk_count ? 'fell' : recent.high_risk_count > previous.high_risk_count ? 'rose' : 'held steady'} from ${previous.high_risk_count} to ${recent.high_risk_count} compared with the previous 30 days.`;
  } else if (activeView === 'calendar') {
    insight = calendarTotal < 5
      ? 'Early signal: the calendar needs more checks before a routine becomes visible.'
      : busiestDay?.count
        ? `Your busiest day was ${new Intl.DateTimeFormat(undefined, { month: 'long', day: 'numeric' }).format(new Date(`${busiestDay.date}T12:00:00`))} with ${busiestDay.count} checks.`
        : 'No daily activity has been recorded in this period.';
  } else {
    const longWeekday = {
      Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday',
      Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday',
    }[busiestWeekday?.weekday];
    insight = weekdayTotal < 5
      ? 'Early signal: a few more checks will make weekday patterns easier to compare.'
      : busiestWeekday?.scam_count
        ? `Most scam checks reached you on ${longWeekday} with ${busiestWeekday.scam_count} checks.`
        : 'No scam checks have been recorded by weekday yet.';
  }

  return (
    <section className="journey__activity-chart-panel" aria-label="Activity over time">
      <div className="journey__activity-chart-head">
        <div><p className="journey__eyebrow">Your timeline</p><h3>When checks happened</h3></div>
        {totalChecks < 3 && <span className="journey__early-signal">Early signal</span>}
      </div>
      <div className="journey__activity-tabs" role="tablist" aria-label="Activity chart view">
        {[
          { key: 'monthly', label: 'Monthly' },
          { key: 'calendar', label: 'Calendar' },
          { key: 'weekday', label: 'Weekday' },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            id={`activity-tab-${tab.key}`}
            aria-selected={activeView === tab.key}
            aria-controls="activity-chart-view"
            className={activeView === tab.key ? 'is-active' : ''}
            onClick={() => setActiveView(tab.key)}
          >{tab.label}</button>
        ))}
      </div>
      <div id="activity-chart-view" className="journey__activity-chart-view" role="tabpanel" aria-labelledby={`activity-tab-${activeView}`}>
        {totalChecks === 0 && <ActivityEmptyState onAnalyze={onAnalyze} />}
        {totalChecks > 0 && activeView === 'monthly' && (monthly.length ? (
          <Suspense fallback={<div className="journey__activity-chart-loading" aria-label="Loading monthly chart" />}>
            <ActivityRecharts mode="monthly" data={monthly} />
          </Suspense>
        ) : <ActivityEmptyState onAnalyze={onAnalyze} message="Monthly activity will appear as you make checks." />)}
        {totalChecks > 0 && activeView === 'calendar' && (
          <div className="journey__calendar-wrap">
            {calendarTotal < 5 && <span className="journey__calendar-early">Early signal · {calendarTotal} checks in this 12-week view</span>}
            <div className="journey__calendar-months" aria-hidden="true">
              {calendarDays.filter((_, index) => index % 7 === 0).map((day, index) => (
                <span key={day.date} style={{ gridColumn: index + 1 }}>{new Intl.DateTimeFormat(undefined, { month: 'short' }).format(new Date(`${day.date}T12:00:00`))}</span>
              ))}
            </div>
            <div className="journey__calendar-layout">
              <div className="journey__calendar-weekdays" aria-hidden="true">{weekdayNames.map((day) => <span key={day}>{day}</span>)}</div>
              <div className="journey__calendar-grid" role="group" aria-label="Daily checks for the last 12 weeks">
                {calendarDays.map((day) => {
                  const date = new Date(`${day.date}T12:00:00`);
                  const intensity = day.count === 0 ? 0 : Math.max(1, Math.ceil((day.count / maxDayCount) * 4));
                  const weekday = new Intl.DateTimeFormat(undefined, { weekday: 'long' }).format(date);
                  const checkLabel = day.count === 1 ? 'check' : 'checks';
                  const label = `${weekday}, ${new Intl.DateTimeFormat(undefined, { month: 'long', day: 'numeric', year: 'numeric' }).format(date)}: ${day.count} ${checkLabel}${day.high_risk_count ? `, ${day.high_risk_count} high risk` : ''}`;
                  return (
                    <button
                      key={day.date}
                      type="button"
                      className={`journey__calendar-cell${day.high_risk_count ? ' has-high-risk' : ''}${selectedDay?.date === day.date ? ' is-selected' : ''}`}
                      data-level={intensity}
                      title={label}
                      aria-label={label}
                      aria-pressed={selectedDay?.date === day.date}
                      disabled={day.date > new Date().toLocaleDateString('en-CA')}
                      onClick={() => setSelectedDay(day)}
                    />
                  );
                })}
              </div>
            </div>
            <div className="journey__calendar-legend" aria-label="Calendar legend">
              <span>Fewer checks</span><i data-level="0" /><i data-level="1" /><i data-level="2" /><i data-level="3" /><i data-level="4" /><span>More checks</span><b><i className="has-high-risk" /> High-risk day</b>
            </div>
            {selectedDay && (
              <div className="journey__calendar-detail" aria-live="polite">
                <strong>{new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date(`${selectedDay.date}T12:00:00`))}</strong>
                {selectedDay.groups?.length ? (
                  <ul>{selectedDay.groups.map((group) => <li key={group.type}><span>{group.type}</span><strong>{group.count} {group.count === 1 ? 'check' : 'checks'}</strong></li>)}</ul>
                ) : <p>No checks recorded on this day.</p>}
              </div>
            )}
          </div>
        )}
        {totalChecks > 0 && activeView === 'weekday' && (
          weekdays.some((day) => day.scam_count > 0)
            ? <Suspense fallback={<div className="journey__activity-chart-loading" aria-label="Loading weekday chart" />}><ActivityRecharts mode="weekday" data={weekdays} /></Suspense>
            : <ActivityEmptyState onAnalyze={onAnalyze} message="No scam-check activity has been recorded by weekday." />
        )}
      </div>
      <p className="journey__activity-insight" aria-live="polite"><span aria-hidden="true">↳</span>{insight}</p>
    </section>
  );
}

function PatternSparkline({ points, type }) {
  const values = points.map((point) => point.count);
  const maxValue = Math.max(...values, 1);
  const coordinates = values.map((value, index) => ({
    x: values.length > 1 ? (index / (values.length - 1)) * 100 : 50,
    y: 30 - (value / maxValue) * 24,
  }));
  const path = coordinates.map((point, index) => `${index ? 'L' : 'M'}${point.x},${point.y}`).join(' ');

  return (
    <svg className="journey__pattern-sparkline" viewBox="0 0 100 34" role="img" aria-label={`${type} scam checks over the last six months`}>
      <path d={path} />
      {coordinates.length > 0 && <circle cx={coordinates[coordinates.length - 1].x} cy={coordinates[coordinates.length - 1].y} r="2.5" />}
    </svg>
  );
}

  const SCAM_TYPE_SUMMARIES = {
    'Banking Access & Payment': {
      summary: 'This scam usually tries to get you to share a password, bank code, card details, or a payment before you verify the request.',
      attackVector: 'It often pretends to be your bank, payment app, or a payment request that feels urgent.',
      advice: 'Contact your bank through the number on your card or the official app. Never use links from the message itself.',
    },
    'Financial and Investment': {
      summary: 'This scam usually promises quick returns, guaranteed profits, or a sure investment opportunity to pressure you to act fast.',
      attackVector: 'It often pushes a “once-in-a-lifetime” investment or loan offer with a fake sense of urgency.',
      advice: 'Independently check the company and delay any transfer until you verify the offer through official channels.',
    },
    'Health and Wellness': {
      summary: 'This scam usually offers a miracle cure, treatment, or health product and asks for money or private details right away.',
      attackVector: 'It often uses fear, hope, or urgency to get you to pay before you pause and verify the claim.',
      advice: 'Use a trusted medical professional and contact the clinic or provider through their official website or phone number.',
    },
    'Impersonation and Authority': {
      summary: 'This scam usually pretends to be a trusted person, agency, company, or authority to make the request feel legitimate.',
      attackVector: 'It often uses fear, deadlines, or a fake identity to pressure you into acting before you verify the contact.',
      advice: 'Contact the real organization through a number or website you already trust. Do not rely on the message itself.',
    },
    'International or Cross-Border': {
      summary: 'This scam usually involves money movement, customs issues, or a foreign transaction that needs a quick payment or personal detail.',
      attackVector: 'It often creates urgency around a shipment, transfer, or import problem that seems highly specific and time-sensitive.',
      advice: 'Pause and verify the request through a trusted, independent source before sending any money or details.',
    },
    'Job, Business, and Work-from-Home': {
      summary: 'This scam usually promises easy money or a job, then asks for a fee, personal data, or banking details before work begins.',
      attackVector: 'It often uses a fake employer, remote-job pitch, or a “quick easy cash” offer.',
      advice: 'Never pay to get a job. Verify the employer through its official website or verified company contact details.',
    },
    'Legal and Document': {
      summary: 'This scam usually threats a fine, legal case, or missed deadline to make you act immediately and reveal private information.',
      attackVector: 'It often sounds official and urgent, using legal pressure or a fake notice to create panic.',
      advice: 'Do not panic or pay through the message. Contact the court, agency, or business through a trusted official channel.',
    },
    'Prize, Raffle & Reward': {
      summary: 'This scam usually claims you won a prize and asks for a fee, bank details, or a link to “claim” it.',
      attackVector: 'It often uses excitement and surprise to push you to click, pay, or share personal information.',
      advice: 'If you did not enter a contest, treat it as suspicious. Do not pay any fee or share banking details.',
    },
    'Property & Rental': {
      summary: 'This scam usually advertises a great property deal and asks for a deposit or payment before the property is verified.',
      attackVector: 'It often uses a too-good-to-be-true listing, a rushed closing, or a fake landlord or agent.',
      advice: 'Verify the property and the landlord independently and never send money before you inspect the listing.',
    },
    'Psychological, Urgency, & Emotional': {
      summary: 'This scam usually uses fear, guilt, panic, or emotional pressure to make you act before you think clearly.',
      attackVector: 'It often makes the message feel personal, urgent, and impossible to ignore in the moment.',
      advice: 'Take a pause, step away from the message, and verify the request through a trusted route before acting.',
    },
    'Romance, Dating, and Relationship': {
      summary: 'This scam usually builds trust and then creates an emergency that asks for money, gift cards, or private information.',
      attackVector: 'It often moves the conversation quickly toward emotional dependence or a crisis requiring fast money.',
      advice: 'Never send money to someone you have not met in person. Speak with a trusted person before acting.',
    },
    'Shopping and E-Commerce': {
      summary: 'This scam usually uses fake stores, impossible discounts, or a checkout link to steal money or card details.',
      attackVector: 'It often targets excitement around a deal, fake delivery update, or a pressure-filled checkout message.',
      advice: 'Use the official retailer website or app directly and avoid paying through unfamiliar links or QR codes.',
    },
    'Tax, Banking, and Loan': {
      summary: 'This scam usually claims you owe money or offers a quick loan and then asks for urgent payment or private information.',
      attackVector: 'It often uses fake tax notices, urgent loan promises, or pressure around a payment that seems time-sensitive.',
      advice: 'Check your account or tax issue through the official website or trusted bank contact, not through the message itself.',
    },
    'Tech and Online Account': {
      summary: 'This scam usually claims an account, device, or password is at risk and asks for a code, password, or remote access.',
      attackVector: 'It often impersonates tech support, a security team, or a provider asking for a one-time code.',
      advice: 'Never share one-time codes or allow remote access. Open the official app or website yourself instead.',
    },
    'Mobile and Digital': {
      summary: 'This scam usually sends a link, code, or message designed to take over your phone, account, or digital wallet.',
      attackVector: 'It often tries to get you to tap a link, install something, or share a verification code quickly.',
      advice: 'Do not open unexpected links or share security codes. Contact your provider through the app or official support channel.',
    },
  };

function getGuidance(type) {
    return SCAM_TYPE_SUMMARIES[type] || {
      summary: 'This scam usually uses urgency, authority, or a valuable offer to make you act before you can verify the request.',
      attackVector: 'It often pressures you to click, pay, or share something quickly without checking the source.',
      advice: 'Pause, do not click or pay, and verify the request through a trusted official contact method.',
  };
}

function Reveal({ children, className = '', delay = 0 }) {
  const elementRef = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return undefined;
    if (!('IntersectionObserver' in window)) {
      setIsVisible(true);
      return undefined;
    }

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true);
        observer.disconnect();
      }
    }, { threshold: 0.16 });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={elementRef}
      className={`journey__reveal ${isVisible ? 'is-visible' : ''} ${className}`}
      style={{ '--reveal-delay': `${delay}ms` }}
    >
      {children}
    </div>
  );
}

function FocusScene({ children, recap, label, direction = 'from-right', className = '' }) {
  return (
    <section className={`journey__focus-scene ${direction} ${className}`} aria-label={label}>
      <div className="journey__focus-detail">{children}</div>
      {recap && <div className="journey__focus-recap">{recap}</div>}
    </section>
  );
}

function formatSubmissionDate(value) {
  if (!value) return 'Date unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date unavailable';
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date);
}

function formatUpdatedAt(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const isToday = date.toDateString() === new Date().toDateString();
  const time = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(date);
  return isToday ? `Updated today at ${time}` : `Updated ${new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date)}`;
}

function formatNextGenerationAt(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return `Another summary will be available after ${new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date)}.`;
}

function formatSummaryMonthYear(value) {
  if (!value) return 'this month';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'this month';
  return new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' }).format(date);
}

function formatSummaryGeneratedDate(value) {
  if (!value) return 'Date unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date unavailable';
  return new Intl.DateTimeFormat(undefined, {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

function AIInsightSection({ insight, loading, error, onRequest }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!insight && !loading) {
    return (
      <section className="journey__ai-insight journey__ai-insight--prompt" aria-labelledby="ai-insight-title">
        <div className="journey__ai-insight-icon" aria-hidden="true">✨</div>
        <div className="journey__ai-insight-body">
          <h2 id="ai-insight-title">Want this explained simply?</h2>
          <p>We can turn your safety summary into a short, plain-language explanation.</p>
          {error && <p className="journey__ai-insight-error">{error}</p>}
          <button type="button" className="journey__ai-insight-button" onClick={onRequest}>
            Explain my summary in plain language
          </button>
        </div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="journey__ai-insight" aria-live="polite">
        <div className="journey__ai-insight-icon" aria-hidden="true">✨</div>
        <div className="journey__ai-insight-body">
          <p className="journey__ai-insight--loading">Putting your summary into plain words...</p>
        </div>
      </section>
    );
  }

  const riskTag = insight.risk_tag || 'low';
  const nextGenerationAt = insight.next_generation_at ? new Date(insight.next_generation_at) : null;
  const canRequestAnother = !nextGenerationAt || Number.isNaN(nextGenerationAt.getTime()) || nextGenerationAt <= new Date();
  const sections = [
    { key: 'current_status', title: 'Where you stand right now', items: insight.current_status },
    { key: 'your_journey', title: 'Your journey so far', items: insight.your_journey },
    { key: 'community_trends', title: "What's happening around you", items: insight.community_trends },
  ];

  return (
    <section className="journey__ai-insight" aria-labelledby="ai-insight-title">
      <div className="journey__ai-insight-icon" aria-hidden="true">✨</div>
      <div className="journey__ai-insight-body">
        <div className="journey__ai-insight-kicker">
          <span>Your summary for {formatSummaryMonthYear(insight.generated_at)}</span>
          <span className={`journey__ai-insight-tag journey__ai-insight-tag--${riskTag}`}>{riskTag} risk</span>
        </div>
        <div className="journey__ai-insight-head">
          <h2 id="ai-insight-title">{insight.headline || 'Your safety at a glance'}</h2>
          <button
            type="button"
            className="journey__ai-insight-toggle"
            onClick={() => setIsExpanded((expanded) => !expanded)}
            aria-expanded={isExpanded}
            aria-controls="ai-insight-details"
          >
            {isExpanded ? 'Hide summary' : 'Show summary'}
          </button>
          <button
            type="button"
            className="journey__ai-insight-button journey__ai-insight-button--secondary"
            onClick={onRequest}
            disabled={!canRequestAnother || loading}
          >
            {canRequestAnother ? 'Request new summary' : 'Monthly refresh used'}
          </button>
        </div>

        <div
          id="ai-insight-details"
          className={`journey__ai-insight-details${isExpanded ? ' journey__ai-insight-details--expanded' : ''}`}
          aria-hidden={!isExpanded}
        >
          <div className="journey__ai-insight-details-inner">
            <p className="journey__ai-insight-generated">Summary generated on {formatSummaryGeneratedDate(insight.generated_at)}.</p>
            {sections.map((section, sectionIndex) => (
              (section.items || []).length > 0 && (
                <article className="journey__ai-insight-section" key={section.key}>
                  <div className="journey__ai-insight-section-heading">
                    <span className="journey__ai-insight-section-number">0{sectionIndex + 1}</span>
                    <p className="journey__ai-insight-section-title">{section.title}</p>
                  </div>
                  <div className="journey__ai-insight-copy">
                    {section.items.map((line, index) => <p key={index}>{line}</p>)}
                  </div>
                </article>
              )
            ))}

            {(insight.watch_list || []).length > 0 && (
              <article className="journey__ai-insight-section journey__ai-insight-section--watch">
                <div className="journey__ai-insight-section-heading">
                  <span className="journey__ai-insight-section-number">0{sections.length + 1}</span>
                  <p className="journey__ai-insight-section-title">What to watch out for</p>
                </div>
                <ul className="journey__ai-insight-watchlist">
                  {insight.watch_list.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </article>
            )}

            {insight.tip && (
              <aside className="journey__ai-insight-tip">
                <span className="journey__ai-insight-tip-mark" aria-hidden="true">→</span>
                <p><strong>One useful next step</strong>{insight.tip}</p>
              </aside>
            )}
            {insight.generated_at && (
              <p className="journey__ai-insight-meta">{formatUpdatedAt(insight.generated_at)}</p>
            )}
            {!canRequestAnother && (
              <p className="journey__ai-insight-meta">{formatNextGenerationAt(insight.next_generation_at)}</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function dedupeRecentSubmissions(submissions = []) {
  const seen = new Map();

  return [...submissions]
    .filter((submission) => {
      const type = String(submission.type || 'Unknown').trim();
      const createdAt = submission.created_at ? String(submission.created_at) : 'no-date';
      const score = Number.isFinite(Number(submission.scam_score)) ? Number(submission.scam_score) : 'na';
      const riskState = submission.is_scam ? 'scam' : 'safe';
      const uniqueKey = submission.ref_id
        ? `ref:${submission.ref_id}`
        : `${type}|${createdAt}|${score}|${riskState}`;

      if (seen.has(uniqueKey)) return false;
      seen.set(uniqueKey, true);
      return true;
    })
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
}

function summarizeRecentSubmissions(submissions = []) {
  const grouped = new Map();

  dedupeRecentSubmissions(submissions).forEach((submission) => {
    const type = String(submission.type || 'Unknown').trim();
    const existing = grouped.get(type);
    const score = Number(submission.scam_score);
    if (!existing) {
      grouped.set(type, {
        ...submission,
        type,
        count: 1,
        highestScore: Number.isFinite(score) ? score : null,
      });
      return;
    }

    existing.count += 1;
    if (Number.isFinite(score) && (existing.highestScore === null || score > existing.highestScore)) {
      existing.highestScore = score;
    }
    if (new Date(submission.created_at || 0) > new Date(existing.created_at || 0)) {
      existing.created_at = submission.created_at;
      existing.is_scam = submission.is_scam;
    }
  });

  return [...grouped.values()].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
}

function buildTypeInsights(personal) {
  const topTypes = personal?.type_insights || personal?.top_types || [];

  if (!topTypes.length) return [];

  return topTypes.map((item) => {
    const guidance = getGuidance(item.type);
    const recentCount = item.recent_count || 0;
    const trendText = item.trend_direction === 'increasing'
      ? `${recentCount} checks in the last 30 days; this pattern is increasing.`
      : item.trend_direction === 'decreasing'
        ? `${recentCount} checks in the last 30 days; this pattern is easing.`
        : recentCount
          ? `${recentCount} checks in the last 30 days; this pattern is steady.`
          : 'This pattern has not appeared in the last 30 days.';

    return {
      ...item,
      avgScore: item.average_scam_score ?? null,
      recentCount,
      trendText,
      description: item.description || `${item.count} total checks • ${item.share}% of your scam checks.`,
      attackText: guidance.attackVector,
      recommendation: guidance.advice,
    };
  });
}

function PatternInsightCarousel({ items, activeIndex, setActiveIndex, onAskGuidance }) {
  const touchStartX = useRef(null);
  if (!items.length) return null;

  const item = items[activeIndex];
  const showPrevious = () => setActiveIndex((current) => (current + items.length - 1) % items.length);
  const showNext = () => setActiveIndex((current) => (current + 1) % items.length);

  return (
    <div
      className="journey__pattern-carousel"
      aria-live="polite"
      onTouchStart={(event) => { touchStartX.current = event.changedTouches[0]?.clientX ?? null; }}
      onTouchEnd={(event) => {
        if (touchStartX.current === null) return;
        const distance = event.changedTouches[0]?.clientX - touchStartX.current;
        if (Math.abs(distance) > 45) setActiveIndex((current) => (current + (distance < 0 ? 1 : items.length - 1)) % items.length);
        touchStartX.current = null;
      }}
    >
      <div className="journey__pattern-carousel-nav">
        <span className="journey__eyebrow">Selected pattern</span>
        <span className="journey__pattern-carousel-count">{activeIndex + 1} / {items.length}</span>
      </div>
      <article className="journey__insight journey__insight--active">
        <div className="journey__insight-header">
          <strong>{item.type}</strong>
          <span className={`journey__trend-chip journey__trend-chip--${item.trend_direction}`}>
            {item.trend_direction === 'increasing' ? '↑ Rising' : item.trend_direction === 'decreasing' ? '↓ Easing' : '→ Steady'}
          </span>
        </div>
        <div className="journey__pattern-stat-tiles">
          <div><span>Share of scam checks</span><strong>{item.share}%</strong></div>
          <div><span>Average scam score</span><strong>{item.avgScore === null ? '—' : `${item.avgScore}%`}</strong></div>
          <div><span>High-risk rate</span><strong>{item.high_risk_rate ?? 0}%</strong></div>
          <div><span>Type confidence</span><strong>{item.average_type_confidence == null ? '—' : `${item.average_type_confidence}%`}</strong></div>
        </div>
        <p>{item.description}</p>
        <p className="journey__insight-attack">{item.attackText}</p>
        <div className="journey__red-flags">
          <span className="journey__red-flags-label">Common red flags</span>
          {item.common_red_flags?.length ? item.common_red_flags.map(({ marker, count }) => (
            <span className="journey__red-flag" key={marker}>{marker}<small>{count}</small></span>
          )) : <span className="journey__red-flags-empty">No repeated flags recorded yet.</span>}
        </div>
        <p className="journey__insight-action"><strong>Safest next step:</strong> {item.recommendation}</p>
        {item.sample_note && <p className="journey__pattern-sample-note">{item.sample_note}</p>}
        <button className="journey__guidance-button" type="button" onClick={() => onAskGuidance(item.type)}>
          Ask Guidance about this <span aria-hidden="true">→</span>
        </button>
      </article>
      <div className="journey__pattern-carousel-controls">
        <button type="button" onClick={showPrevious} aria-label="Show previous pattern">←</button>
        <div className="journey__pattern-carousel-dots" role="tablist" aria-label="Pattern details">
          {items.map((pattern, index) => (
            <button
              key={pattern.type}
              type="button"
              role="tab"
              aria-selected={activeIndex === index}
              className={activeIndex === index ? 'is-active' : ''}
              onClick={() => setActiveIndex(index)}
              aria-label={`Show ${pattern.type} details`}
            />
          ))}
        </div>
        <button type="button" onClick={showNext} aria-label="Show next pattern">→</button>
      </div>
    </div>
  );
}

function PatternHero({ item, totalChecks, onAskGuidance }) {
  if (!item) return null;

  const trendLabel = item.trend_direction === 'increasing' ? 'Rising' : item.trend_direction === 'decreasing' ? 'Easing' : 'Steady';
  return (
    <article className="journey__check-hero">
      <div className="journey__check-hero-main">
        <p className="journey__eyebrow">Your strongest pattern</p>
        <h3>{item.type}</h3>
        <p>{item.description}</p>
        <div className="journey__check-hero-stats">
          <span><strong>{item.count}</strong> checks</span>
          <span><strong>{item.share}%</strong> of scam checks</span>
          <span className={`journey__trend-chip journey__trend-chip--${item.trend_direction}`}>{trendLabel}</span>
        </div>
        {totalChecks < 3 && <span className="journey__early-signal">Early signal</span>}
        <button className="journey__guidance-button" type="button" onClick={() => onAskGuidance(item.type)}>
          Ask Guidance about this <span aria-hidden="true">→</span>
        </button>
      </div>
      <div className="journey__check-hero-chart">
        <span>Last 6 months</span>
        <PatternSparkline points={item.monthly_counts || []} type={item.type} />
        <div className="journey__sparkline-months">
          {(item.monthly_counts || []).map((point) => <span key={point.month}>{point.label}</span>)}
        </div>
      </div>
    </article>
  );
}

function PatternSignalBoard({ items, onAskGuidance, onAnalyze }) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    setActiveIndex((current) => Math.min(current, Math.max(items.length - 1, 0)));
  }, [items.length]);

  if (!items.length) {
    return (
      <div className="journey__signal-empty">
        <p>No scam patterns have appeared in your checks yet.</p>
        <button className="journey__guidance-button" type="button" onClick={onAnalyze}>Analyze a message <span aria-hidden="true">→</span></button>
      </div>
    );
  }

  return (
    <div className="journey__signal-board">
      <div className="journey__signal-list" aria-label="Your scam pattern ranking">
        <div className="journey__signal-list-heading">
          <div><p className="journey__eyebrow">Pattern mix</p><strong>Top 3 by frequency</strong></div>
          <span>Ranked by frequency</span>
        </div>
        {items.map((item, index) => (
          <button
            className={`journey__signal-row ${activeIndex === index ? 'is-active' : ''}`}
            type="button"
            key={item.type}
            onClick={() => setActiveIndex(index)}
            aria-pressed={activeIndex === index}
          >
            <span className="journey__signal-rank">0{index + 1}</span>
            <span className="journey__signal-copy">
              <strong>{item.type}</strong>
              <span>{item.count} {item.count === 1 ? 'check' : 'checks'} · {item.share}% share</span>
            </span>
            <span className="journey__signal-meter"><span style={{ width: `${Math.max((item.count / items[0].count) * 100, 8)}%` }} /></span>
            <span className={`journey__signal-status journey__signal-status--${item.trend_direction}`}>
              <span aria-hidden="true">{item.trend_direction === 'increasing' ? '↑' : item.trend_direction === 'decreasing' ? '↓' : '→'}</span>{' '}
              {item.trend_direction === 'increasing' ? 'Rising' : item.trend_direction === 'decreasing' ? 'Easing' : 'Steady'}
            </span>
          </button>
        ))}
      </div>
      <PatternInsightCarousel items={items} activeIndex={activeIndex} setActiveIndex={setActiveIndex} onAskGuidance={onAskGuidance} />
    </div>
  );
}

function AdviceCarousel({ community, personal, onAskGuidance }) {
  const [slide, setSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const risingType = community?.community_analytics?.rising_scams?.[0]?.type;
  const userType = personal?.top_types?.[0]?.type;
  const cards = [
    ...(risingType ? [{
      title: `${risingType} is rising`,
      body: `${community.community_analytics.rising_scams[0].change_percent ?? 'New'}${community.community_analytics.rising_scams[0].change_percent == null ? '' : '%'} more reports than last month. ${getGuidance(risingType).advice}`,
      category: risingType,
      tag: 'Community alert',
    }] : []),
    ...(userType && userType !== risingType ? [{
      title: `Check ${userType} independently`,
      body: getGuidance(userType).advice,
      category: userType,
      tag: 'Your top pattern',
    }] : []),
    ...(community?.seasonal_insight ? [{
      title: 'Seasonal reminder',
      body: community.seasonal_insight,
      category: null,
      tag: 'Seasonal',
    }] : []),
    {
      title: 'Pause before you respond',
      body: 'Avoid links and contact details inside unexpected messages. Open the official app or website yourself to verify the request.',
      category: null,
      tag: 'General safety',
    },
  ];

  useEffect(() => {
    if (isPaused || cards.length < 2) return undefined;
    const timer = window.setInterval(() => setSlide((current) => (current + 1) % cards.length), 8000);
    return () => window.clearInterval(timer);
  }, [cards.length, isPaused]);

  useEffect(() => setSlide((current) => Math.min(current, cards.length - 1)), [cards.length]);

  const showNext = () => setSlide((current) => (current + 1) % cards.length);
  const showPrevious = () => setSlide((current) => (current + cards.length - 1) % cards.length);
  const activeCard = cards[slide];

  return (
    <div
      className="journey__advice"
      aria-live="polite"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={() => setIsPaused(true)}
      onTouchEnd={() => setIsPaused(false)}
    >
      <div className="journey__advice-topline">
        <span className="journey__eyebrow">Community advice</span>
        <span className="journey__advice-count">{slide + 1} / {cards.length}</span>
      </div>
      <div className="journey__advice-body">
        <span className="journey__advice-tag">{activeCard.tag}</span>
        <h3>{activeCard.title}</h3>
        <p>{activeCard.body}</p>
        <button type="button" className="journey__advice-guidance" onClick={() => onAskGuidance(activeCard.category)}>
          Ask Guidance <span aria-hidden="true">→</span>
        </button>
      </div>
      <div className="journey__advice-controls">
        <button type="button" onClick={showPrevious} aria-label="Show previous advice">←</button>
        <div className="journey__advice-dots" aria-label="Advice slides">
          {cards.map((card, index) => <button key={`${card.tag}-${card.title}`} className={slide === index ? 'is-active' : ''} type="button" onClick={() => setSlide(index)} aria-label={`Show advice ${index + 1}: ${card.tag}`} />)}
        </div>
        <button type="button" onClick={showNext} aria-label="Show next advice">→</button>
      </div>
    </div>
  );
}

function CommunityShareComparison({ personal, community }) {
  const userTypes = personal?.top_types || [];
  const communityTypes = community?.community_analytics?.top_types_all_time || [];
  const userByType = new Map(userTypes.map((item) => [item.type, item.share]));
  const communityByType = new Map(communityTypes.map((item) => [item.type, item.share]));
  const categories = [...new Set([...communityTypes, ...userTypes].map((item) => item.type))]
    .sort((a, b) => (communityByType.get(b) || 0) - (communityByType.get(a) || 0))
    .slice(0, 5);
  const rows = categories.map((type) => ({
    type,
    userShare: userByType.get(type) || 0,
    communityShare: communityByType.has(type) ? communityByType.get(type) : null,
  }));
  const leadingComparison = rows
    .filter((row) => row.communityShare > 0 && row.userShare > row.communityShare)
    .sort((a, b) => b.userShare / b.communityShare - a.userShare / a.communityShare)[0];
  const insight = leadingComparison
    ? `You see ${leadingComparison.type} ${(leadingComparison.userShare / leadingComparison.communityShare).toFixed(1)}× more than the community average.`
    : rows.some((row) => row.communityShare !== null)
      ? 'Your pattern mix is broadly in line with the visible community trends.'
      : 'Not enough community data to compare patterns yet.';

  return (
    <section className="journey__community-compare-chart" aria-labelledby="community-compare-title">
      <div className="journey__community-card-heading">
        <div><p className="journey__eyebrow">You vs community</p><h3 id="community-compare-title">Share of scam checks</h3></div>
        <span>Top 5 patterns</span>
      </div>
      {rows.length ? (
        <div className="journey__compare-bars" role="img" aria-label="Your share compared with the community for the top scam categories">
          <div className="journey__compare-axis" aria-hidden="true"><span>Category</span><div><i>0%</i><i>25%</i><i>50%</i><i>75%</i><i>100%</i></div></div>
          {rows.map((row) => (
            <div className="journey__compare-category" key={row.type}>
              <strong title={row.type}>{row.type}</strong>
              <div className="journey__compare-pair">
                <div className="journey__compare-track" aria-label={`You: ${row.userShare}%`}><span className="journey__compare-fill journey__compare-fill--you" style={{ width: `${row.userShare}%` }} /></div>
                <b>{row.userShare}%</b>
                <div className="journey__compare-track" aria-label={`Community: ${row.communityShare === null ? 'not enough data' : `${row.communityShare}%`}`}><span className="journey__compare-fill journey__compare-fill--community" style={{ width: `${row.communityShare || 0}%` }} /></div>
                <b>{row.communityShare === null ? 'Not enough data' : `${row.communityShare}%`}</b>
              </div>
            </div>
          ))}
          <div className="journey__compare-legend"><span><i className="is-you" /> You</span><span><i className="is-community" /> Community</span></div>
        </div>
      ) : <p className="journey__community-empty">Not enough data to compare patterns yet.</p>}
      <p className="journey__community-insight">{insight}</p>
    </section>
  );
}

function CommunityCategoryChart({ community, onAskGuidance }) {
  const [range, setRange] = useState('all_time');
  const items = range === 'this_month'
    ? community?.community_analytics?.top_types_this_month || []
    : community?.community_analytics?.top_types_all_time || [];
  const maxShare = Math.max(...items.map((item) => item.share), 1);

  return (
    <section className="journey__community-card" aria-labelledby="community-category-title">
      <div className="journey__community-card-heading">
        <div><p className="journey__eyebrow">Ranked categories</p><h3 id="community-category-title">Community scam patterns</h3></div>
        <div className="journey__segmented-control" aria-label="Community category period">
          <button type="button" className={range === 'this_month' ? 'is-active' : ''} aria-pressed={range === 'this_month'} onClick={() => setRange('this_month')}>This month</button>
          <button type="button" className={range === 'all_time' ? 'is-active' : ''} aria-pressed={range === 'all_time'} onClick={() => setRange('all_time')}>All time</button>
        </div>
      </div>
      {items.length ? (
        <div className="journey__community-rankings" role="list" aria-label={`${range === 'all_time' ? 'All time' : 'This month'} community scam category shares`}>
          {items.map((item, index) => (
            <div className="journey__community-rank-row" key={item.type} role="listitem">
              <span className="journey__community-rank">0{index + 1}</span>
              <button type="button" className="journey__community-rank-type" onClick={() => onAskGuidance(item.type)}>{item.type}<span aria-hidden="true">↗</span></button>
              <div className="journey__community-rank-track" aria-label={`${item.share}% of community scam checks`}><span style={{ width: `${(item.share / maxShare) * 100}%` }} /></div>
              <strong>{item.share}%</strong>
            </div>
          ))}
        </div>
      ) : <p className="journey__community-empty">Not enough data to show this period.</p>}
    </section>
  );
}

function CommunityTrendChart({ community, personal }) {
  const [selectedCategoryState, setSelectedCategory] = useState('');
  const analytics = community?.community_analytics;
  const personalTypes = personal?.type_insights || [];
  const communityTypes = analytics?.category_monthly_series || analytics?.top_types_all_time || [];
  const categories = [...new Set([
    ...personalTypes.slice(0, 5).map((item) => item.type),
    ...communityTypes.map((item) => item.type),
  ])];
  const selectedCategory = selectedCategoryState || analytics?.top_types_all_time?.[0]?.type || personalTypes[0]?.type || communityTypes[0]?.type || '';
  const personalType = personalTypes.find((item) => item.type === selectedCategory);
  const communityType = communityTypes.find((item) => item.type === selectedCategory);
  const personalCategoryMonths = new Map((personalType?.monthly_counts || []).map((item) => [item.month, item]));
  const personalActivityMonths = new Map((personal?.activity?.monthly_risk || []).map((item) => [item.month, item]));
  const communityCategoryMonths = new Map((communityType?.monthly_counts || []).map((item) => [item.month, item]));
  const communityTotals = new Map((analytics?.monthly_confirmed_scams || []).map((item) => [item.month, item]));
  const monthPoints = (communityType?.monthly_counts || personalType?.monthly_counts || []).slice(-6);
  const comparisonPoints = monthPoints.map((month) => {
    const personalMonth = personalActivityMonths.get(month.month);
    const personalScamTotal = personalMonth ? personalMonth.suspicious + personalMonth.high_risk : 0;
    const personalCategoryCount = personalCategoryMonths.get(month.month)?.count ?? 0;
    const communityMonth = communityCategoryMonths.get(month.month);
    const communityTotal = communityTotals.get(month.month);

    return {
      ...month,
      user_share: personalScamTotal > 0 ? (personalCategoryCount / personalScamTotal) * 100 : null,
      community_share: communityMonth?.count != null && communityTotal?.count > 0
        ? (communityMonth.count / communityTotal.count) * 100
        : null,
    };
  });
  const hasVisiblePoints = comparisonPoints.some((point) => point.user_share !== null || point.community_share !== null);

  return (
    <section className="journey__community-card" aria-labelledby="community-trend-title">
      <div className="journey__community-card-heading">
        <div><p className="journey__eyebrow">You vs community</p><h3 id="community-trend-title">Pattern prominence over time</h3></div>
        <label className="journey__community-filter">Category
          <select value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value)}>
            {categories.map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
        </label>
      </div>
      {hasVisiblePoints ? (
        <Suspense fallback={<div className="journey__community-chart-loading" aria-label="Loading You versus Community chart" />}>
          <CommunityLineChart data={comparisonPoints} category={selectedCategory} />
        </Suspense>
      ) : <p className="journey__community-empty">Not enough history to compare this pattern yet. Community months with fewer than five distinct users remain hidden.</p>}
      <div className="journey__community-line-legend" aria-label="Chart series">
        <span><i className="journey__community-line-legend-you" /> You</span>
        <span><i className="journey__community-line-legend-community" /> Community</span>
      </div>
    </section>
  );
}

function CommunitySection({ community, personal, onAskGuidance, onAnalyze }) {
  const analytics = community?.community_analytics;
  const risingScams = analytics?.rising_scams || [];

  return (
    <section className="journey__community">
      <div className="journey__section-heading">
        <div><p className="journey__eyebrow">03 / Everyone using Verif-AI</p><h2>What is happening around you?</h2><p>Community patterns help put your checks in context.</p></div>
        <div className="journey__section-header-right">
          <span className="journey__community-rate">{community?.scam_rate ?? 0}% flagged</span>
          <span className="journey__section-number">03</span>
        </div>
      </div>
      <div className="journey__community-overview">
        <p className="journey__community-summary">{community?.summary || 'Community trends are still being collected.'}</p>
        <span className="journey__community-users">Based on {analytics?.distinct_users ?? 0} users&apos; checks</span>
        {analytics?.has_demo_data && <span className="journey__community-demo-badge">Presentation demo data included</span>}
      </div>
      <CommunityShareComparison personal={personal} community={community} />
      <section className="journey__rising-section" aria-labelledby="rising-scams-title">
        <div className="journey__community-card-heading"><div><p className="journey__eyebrow">Month-over-month movement</p><h3 id="rising-scams-title">Rising scams</h3></div><span>Top 5</span></div>
        {risingScams.length ? (
          <ol className="journey__rising-list">
            {risingScams.map((item, index) => (
              <li key={item.type}>
                <span className="journey__community-rank">0{index + 1}</span>
                <strong>{item.type}</strong>
                <span className={`journey__rising-change${item.is_new ? ' is-new' : ''}`}>{item.is_new ? 'New' : `${item.change_percent > 0 ? '↑ ' : item.change_percent < 0 ? '↓ ' : ''}${Math.abs(item.change_percent)}%`}</span>
                <CommunitySparkline points={item.monthly_counts} type={item.type} />
                <button type="button" onClick={() => onAskGuidance(item.type)}>Learn more <span aria-hidden="true">→</span></button>
              </li>
            ))}
          </ol>
        ) : <p className="journey__community-empty">Not enough data for a month-over-month community signal yet.</p>}
      </section>
      <AdviceCarousel community={community} personal={personal} onAskGuidance={onAskGuidance} />
      <div className="journey__community-grid">
        <CommunityCategoryChart community={community} onAskGuidance={onAskGuidance} />
        <CommunityTrendChart community={community} personal={personal} />
      </div>
      <p className="journey__community-privacy">Community data is anonymized and aggregated. Categories and month buckets with fewer than five distinct users are hidden.</p>
      {!community?.total_checks && <button className="journey__community-analyze" type="button" onClick={onAnalyze}>Analyze a message <span aria-hidden="true">→</span></button>}
    </section>
  );
}

function CommunitySparkline({ points = [], type }) {
  const validPoints = points.map((point) => point.count == null ? null : point.count);
  const maxCount = Math.max(...validPoints.filter((value) => value !== null), 1);
  const path = validPoints.map((value, index) => {
    if (value === null) return '';
    const x = validPoints.length > 1 ? (index / (validPoints.length - 1)) * 100 : 50;
    const y = 28 - (value / maxCount) * 22;
    return `${index === 0 || validPoints[index - 1] === null ? 'M' : 'L'}${x},${y}`;
  }).filter(Boolean).join(' ');

  return path
    ? <svg className="journey__community-sparkline" viewBox="0 0 100 32" role="img" aria-label={`${type} monthly trend`}><path d={path} /></svg>
    : <span className="journey__rising-no-data">Not enough data</span>;
}

export default function Analytics() {
  const navigate = useNavigate();
  const { user, isLoggedIn, isAdmin, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [personal, setPersonal] = useState(null);
  const [community, setCommunity] = useState(null);
  const [activityView, setActivityView] = useState('monthly');
  const [selectedActivityDay, setSelectedActivityDay] = useState(null);
  const [aiInsight, setAiInsight] = useState(null);
  const [aiInsightLoading, setAiInsightLoading] = useState(false);
  const [aiInsightError, setAiInsightError] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const checkPatterns = buildTypeInsights(personal).slice(0, 3);

  const askGuidance = (category) => {
    navigate('/chatbot', { state: { guidanceCategory: category } });
  };

  const handleLogout = async () => {
    await logout();
    setShowUserMenu(false);
    navigate('/');
  };

  const requestAiInsight = () => {
    setAiInsightLoading(true);
    setAiInsightError('');
    getUserAiSummary()
      .then((response) => {
        if (response?.data?.success) {
          setAiInsight(response.data.data);
        } else {
          setAiInsightError('We could not build your summary. Please try again.');
        }
      })
      .catch(() => setAiInsightError('We could not build your summary. Please try again.'))
      .finally(() => setAiInsightLoading(false));
  };

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/login', { replace: true });
      return;
    }

    // Reuse recent data when revisiting the page instead of hitting the API every time.
    const owner = user?.username || user?.email || '';
    if (analyticsCache && analyticsCache.owner !== owner) analyticsCache = null;
    const cached = analyticsCache;
    if (cached) {
      setPersonal(cached.personal);
      setCommunity(cached.community);
      if (cached.aiInsight) setAiInsight(cached.aiInsight);
      setLoading(false);
      if (Date.now() - cached.at < ANALYTICS_CACHE_TTL_MS) return;
    }

    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    Promise.all([getUserSafetySummary(timezone), getGlobalSafetySummary(timezone)])
      .then(([personalResponse, communityResponse]) => {
        if (personalResponse?.data?.success) setPersonal(personalResponse.data.data);
        if (communityResponse?.data?.success) setCommunity(communityResponse.data.data);
        if (personalResponse?.data?.success && communityResponse?.data?.success) {
          analyticsCache = {
            personal: personalResponse.data.data,
            community: communityResponse.data.data,
            aiInsight: analyticsCache?.aiInsight || null,
            owner: user?.username || user?.email || '',
            at: Date.now(),
          };
        }
      })
      .catch((requestError) => setError(requestError.message || 'We could not load your analytics.'))
      .finally(() => setLoading(false));

    // Show a previously generated summary immediately, if one exists, without calling Gemini again.
    getUserAiSummaryCached()
      .then((response) => {
        if (response?.data?.success && response.data.data) {
          setAiInsight(response.data.data);
          if (analyticsCache) analyticsCache.aiInsight = response.data.data;
        }
      })
      .catch(() => {});
  }, [isLoggedIn, navigate]);

  if (!isLoggedIn) return null;

  return (
    <div className="journey page-enter">
      <header className="nav nav--app">
        <AppNavLinks active="journey" />
        <div className="journey__actions">
          <div className="nav__user-menu" onClick={(event) => event.stopPropagation()}>
            <button
              className="nav__login"
              type="button"
              onClick={() => setShowUserMenu((visible) => !visible)}
            >
              {user?.username || user?.email || 'Profile'}
            </button>
            {showUserMenu && (
              <div className="nav__dropdown">
                <button
                  className="nav__dropdown-item"
                  type="button"
                  onClick={() => { navigate('/settings'); setShowUserMenu(false); }}
                >
                  Settings
                </button>
                {isAdmin && (
                  <button
                    className="nav__dropdown-item nav__dropdown-item--admin"
                    type="button"
                    onClick={() => { navigate('/admin'); setShowUserMenu(false); }}
                  >
                    Admin Dashboard
                  </button>
                )}
                <button
                  className="nav__dropdown-item nav__dropdown-item--logout"
                  type="button"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="journey__content">
        <section className="journey__intro">
          <p className="journey__eyebrow">Your time at Verif-AI</p>
          <h1>Understand what you&apos;re seeing.</h1>
          <p>See your checking habits, the scam patterns around you, and the simple steps that can help you stay safer.</p>
        </section>

        {loading ? (
          <div className="journey__loading">Preparing your safety journey...</div>
        ) : error ? (
          <div className="journey__error">{error}</div>
        ) : (
          <>
            <Reveal>
              <section className="journey__summary" aria-labelledby="safety-summary-title">
                <div className="journey__summary-icon" aria-hidden="true">✦</div>
                <div>
                  <p className="journey__eyebrow">Your safety summary</p>
                  <h2 id="safety-summary-title">{personal?.risk_level || 'No data yet'}</h2>
                  <p>{personal?.summary || 'Check a message to start building your safety summary.'}</p>
                  <p className="journey__scope-note">{personal?.analytics_scope_note || 'Based only on your authenticated Verif-AI checks.'}</p>
                </div>
              </section>
            </Reveal>

            <Reveal className="journey__reveal--wide" delay={80}>
              <AIInsightSection
                insight={aiInsight}
                loading={aiInsightLoading}
                error={aiInsightError}
                onRequest={requestAiInsight}
              />
            </Reveal>

            <Reveal className="journey__reveal--wide" delay={80}>
              <section className="journey__stat-grid" aria-label="Your detection totals">
                <div className="journey__stat"><span>Messages checked</span><strong>{personal?.total_checks ?? 0}</strong></div>
                <div className="journey__stat journey__stat--alert"><span>High-risk results</span><strong>{personal?.high_risk_count ?? 0}</strong></div>
                <div className="journey__stat"><span>Most common pattern</span><strong>{personal?.most_common_type || 'Not enough data'}</strong></div>
              </section>
            </Reveal>

            <Reveal className="journey__reveal--wide" delay={120}>
              <FocusScene
                label="Your most common scam patterns"
                direction="from-right"
                className="journey__checks-scene"
              >
                <div className="journey__section-heading">
                  <div><p className="journey__eyebrow">01 / Your checks</p><h2>What are you running into?</h2><p>These are the scam patterns appearing most often in your authenticated checks.</p></div>
                  <span className="journey__section-number">01</span>
                </div>
                <PatternHero item={checkPatterns[0]} totalChecks={personal?.total_checks ?? 0} onAskGuidance={askGuidance} />
                <PatternSignalBoard
                  items={checkPatterns}
                  totalChecks={personal?.total_checks ?? 0}
                  totalScamChecks={personal?.total_scam_checks ?? 0}
                  onAskGuidance={askGuidance}
                  onAnalyze={() => navigate('/detection')}
                />
              </FocusScene>
            </Reveal>

            <Reveal className="journey__reveal--wide" delay={120}>
              <FocusScene
                label="Your checking activity"
                direction="from-left"
                className="journey__activity-scene"
              >
                <div className="journey__section-heading">
                  <div><p className="journey__eyebrow">02 / Your activity</p><h2>Is your situation changing?</h2><p>Volume matters, but the direction of your high-risk results matters more.</p></div>
                  <span className="journey__section-number">02</span>
                </div>
                <ActivityStatusRow activity={personal?.activity} personal={personal} />
                <div className="journey__activity-dashboard">
                  <ActivityChartPanel
                    activity={personal?.activity}
                    activeView={activityView}
                    setActiveView={setActivityView}
                    selectedDay={selectedActivityDay}
                    setSelectedDay={setSelectedActivityDay}
                    totalChecks={personal?.total_checks ?? 0}
                    onAnalyze={() => navigate('/detection')}
                  />
                  <ActivityRiskMix
                    activity={personal?.activity}
                    totalChecks={personal?.total_checks ?? 0}
                    onAnalyze={() => navigate('/detection')}
                  />
                </div>
              </FocusScene>
            </Reveal>

            <Reveal className="journey__reveal--wide" delay={120}>
              <CommunitySection
                community={community}
                personal={personal}
                onAskGuidance={askGuidance}
                onAnalyze={() => navigate('/detection')}
              />
            </Reveal>
          </>
        )}
      </main>
    </div>
  );
}
