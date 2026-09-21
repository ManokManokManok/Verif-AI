import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Analytics.css';
import { useAuth } from '../context/AuthContext';
import { getUserSafetySummary, getGlobalSafetySummary } from '../api/analytics';

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

function FocusScene({ children, recap, label, direction = 'from-right' }) {
  return (
    <section className={`journey__focus-scene ${direction}`} aria-label={label}>
      <div className="journey__focus-detail">{children}</div>
      <div className="journey__focus-recap">{recap}</div>
    </section>
  );
}

function formatSubmissionDate(value) {
  if (!value) return 'Date unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date unavailable';
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date);
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

function PatternInsightCarousel({ items, activeIndex, setActiveIndex }) {
  if (!items.length) return null;

  const item = items[activeIndex];
  const showPrevious = () => setActiveIndex((current) => (current + items.length - 1) % items.length);
  const showNext = () => setActiveIndex((current) => (current + 1) % items.length);

  return (
    <div className="journey__pattern-carousel" aria-live="polite">
      <div className="journey__pattern-carousel-nav">
        <span className="journey__eyebrow">Pattern details</span>
        <span className="journey__pattern-carousel-count">{activeIndex + 1} / {items.length}</span>
      </div>
      <article className="journey__insight journey__insight--active">
        <div className="journey__insight-header">
          <strong>{item.type}</strong>
          <span className="journey__insight-score">{item.avgScore !== null ? `${item.avgScore}% risk` : `${item.count} checks`}</span>
        </div>
        <p><b>{item.count} checks</b> · {item.share}% of your scam checks · {item.high_risk_rate ?? item.avgScore ?? 0}% high risk.</p>
        <p>{item.description}</p>
        <p className="journey__insight-attack">{item.attackText}</p>
        <div className="journey__insight-meta">
          <span>{item.trendText}</span>
          {item.sample_note && <span>{item.sample_note}</span>}
        </div>
        <p className="journey__insight-action"><strong>Safest next step:</strong> {item.recommendation}</p>
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

function PatternSignalBoard({ items }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeItem = items[activeIndex];
  const totalScamChecks = items.reduce((sum, item) => sum + item.count, 0);

  useEffect(() => {
    setActiveIndex((current) => Math.min(current, Math.max(items.length - 1, 0)));
  }, [items.length]);

  if (!items.length) return <p className="journey__empty">Your scam patterns will appear here after you check messages.</p>;

  return (
    <div className="journey__signal-board">
      <div className="journey__signal-list" aria-label="Your scam pattern ranking">
        <div className="journey__signal-list-heading">
          <div><p className="journey__eyebrow">Pattern mix</p><strong>{totalScamChecks} scam checks</strong></div>
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
              <span>{item.count} {item.count === 1 ? 'check' : 'checks'} · {item.share}%</span>
            </span>
            <span className="journey__signal-meter"><span style={{ width: `${Math.max((item.count / items[0].count) * 100, 8)}%` }} /></span>
            <span className="journey__signal-status">{item.trend_direction === 'increasing' ? 'Rising' : item.trend_direction === 'decreasing' ? 'Easing' : 'Steady'}</span>
          </button>
        ))}
      </div>
      <PatternInsightCarousel items={items} activeIndex={activeIndex} setActiveIndex={setActiveIndex} />
      <div className="journey__signal-callout">
        <span className="journey__eyebrow">What this tells you</span>
        <p><strong>{activeItem.type}</strong> is the pattern appearing most often in your scam checks. Focus on its warning signs before moving to the next message.</p>
      </div>
    </div>
  );
}

function AdviceCarousel({ community }) {
  const [slide, setSlide] = useState(0);
  const leadingType = community?.top_types?.[0]?.type;
  const guidance = getGuidance(leadingType);
  const hasTrend = Boolean(community?.trend_insight || community?.seasonal_insight || leadingType);
  const trendText = community?.trend_insight || (leadingType
      ? `${leadingType} is the most common scam pattern in recent checks.`
    : 'New community scam patterns will appear here as more checks are made.');
  const seasonalText = community?.seasonal_insight;

  useEffect(() => {
    if (!hasTrend) return undefined;
    const timer = window.setInterval(() => setSlide((current) => (current + 1) % 2), 6500);
    return () => window.clearInterval(timer);
  }, [hasTrend]);

  const showNext = () => setSlide((current) => (current + 1) % 2);
  const showPrevious = () => setSlide((current) => (current + 2 - 1) % 2);

  return (
    <div className="journey__advice" aria-live="polite">
      <div className="journey__advice-topline">
        <span className="journey__eyebrow">What to watch for</span>
        <span className="journey__advice-count">{slide + 1} / 2</span>
      </div>
      <div className="journey__advice-body">
        {slide === 0 ? (
          <>
            <h3>{leadingType ? `${leadingType} needs extra attention` : 'A pattern worth watching'}</h3>
            <p>{trendText}</p>
            {seasonalText && <p className="journey__advice-season">{seasonalText}</p>}
          </>
        ) : (
          <>
            <h3>What they may try</h3>
              <p>{guidance.attackVector}</p>
            <p className="journey__advice-next"><strong>Your safest next step:</strong> {guidance.advice}</p>
          </>
        )}
      </div>
      <div className="journey__advice-controls">
        <button type="button" onClick={showPrevious} aria-label="Show previous advice">←</button>
        <div className="journey__advice-dots" aria-label="Advice slides">
          {[0, 1].map((index) => <button key={index} className={slide === index ? 'is-active' : ''} type="button" onClick={() => setSlide(index)} aria-label={`Show advice ${index + 1}`} />)}
        </div>
        <button type="button" onClick={showNext} aria-label="Show next advice">→</button>
      </div>
    </div>
  );
}

export default function Analytics() {
  const navigate = useNavigate();
  const { isLoggedIn, isAdmin } = useAuth();
  const [personal, setPersonal] = useState(null);
  const [community, setCommunity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/login', { replace: true });
      return;
    }

    Promise.all([getUserSafetySummary(), getGlobalSafetySummary()])
      .then(([personalResponse, communityResponse]) => {
        if (personalResponse?.data?.success) setPersonal(personalResponse.data.data);
        if (communityResponse?.data?.success) setCommunity(communityResponse.data.data);
      })
      .catch((requestError) => setError(requestError.message || 'We could not load your safety journey.'))
      .finally(() => setLoading(false));
  }, [isLoggedIn, navigate]);

  if (!isLoggedIn) return null;

  return (
    <div className="journey page-enter">
      <header className="nav nav--journey">
        <div className="brand brand--small">Verif-AI</div>
        <nav className="nav__links">
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/')}>About us</button>
          <button className="nav__link nav__btn nav__btn--active" type="button">Your Verif-AI Journey</button>
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/detection')}>Detection</button>
          <button className="nav__link nav__btn" type="button" onClick={() => navigate('/chatbot')}>AI Chatbot</button>
        </nav>
        <div className="journey__actions">
          <button className="journey__settings" type="button" onClick={() => navigate('/settings')}>Settings</button>
          {isAdmin && <button className="journey__settings" type="button" onClick={() => navigate('/admin')}>Admin</button>}
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
                recap={(
                  <div className="journey__compact-line">
                    <span className="journey__eyebrow">Your pattern</span>
                    <strong>{personal?.most_common_type || 'No pattern yet'}</strong>
                    <span className="journey__mini-pill">{personal?.top_types?.[0]?.count || 0} checks</span>
                  </div>
                )}
              >
                <div className="journey__section-heading">
                  <div><p className="journey__eyebrow">01 / Your checks</p><h2>What are you running into?</h2><p>These are the scam patterns appearing most often in your authenticated checks.</p></div>
                  <span className="journey__section-number">01</span>
                </div>
                {personal?.type_insights?.[0] && (
                  <div className="journey__pattern-lead">
                    <div>
                      <p className="journey__eyebrow">Your strongest pattern</p>
                      <h3>{personal.type_insights[0].type}</h3>
                      <p>{personal.type_insights[0].description}</p>
                    </div>
                    <div className="journey__pattern-lead-stat"><strong>{personal.type_insights[0].count}</strong><span>checks</span></div>
                    <div className="journey__pattern-lead-stat"><strong>{personal.type_insights[0].share}%</strong><span>of scam checks</span></div>
                    <div className="journey__pattern-lead-stat"><strong>{personal.type_insights[0].recent_count || 0}</strong><span>in 30 days</span></div>
                  </div>
                )}
                <PatternSignalBoard items={buildTypeInsights(personal).slice(0, 3)} />
                <div className="journey__submission-strip">
                  <div><p className="journey__eyebrow">Recent patterns</p><h3>What your latest checks have been showing</h3></div>
                    <div className="journey__submission-list">
                    {summarizeRecentSubmissions(personal?.recent_submissions || []).slice(0, 4).map((submission) => (
                      <div className="journey__submission" key={`${submission.ref_id || submission.type}-${submission.created_at}`}>
                        <span className={submission.is_scam ? 'is-risk' : 'is-clear'} aria-hidden="true" />
                        <div><strong>{submission.type}</strong><span>{submission.count} checks · latest {formatSubmissionDate(submission.created_at)}</span></div>
                        <b>{submission.highestScore ?? '--'}% max</b>
                      </div>
                    ))}
                  </div>
                </div>
              </FocusScene>
            </Reveal>

            <Reveal className="journey__reveal--wide" delay={120}>
              <FocusScene
                label="Your checking activity"
                direction="from-left"
                recap={(
                  <div className="journey__compact-line">
                    <span className="journey__eyebrow">Your activity</span>
                    <strong>{personal?.high_risk_rate ?? 0}% high risk</strong>
                    <span className="journey__mini-pill journey__mini-pill--secondary">{personal?.trend?.length || 0} months tracked</span>
                  </div>
                )}
              >
                <div className="journey__section-heading">
                  <div><p className="journey__eyebrow">02 / Your activity</p><h2>Is your situation changing?</h2><p>Volume matters, but the direction of your high-risk results matters more.</p></div>
                  <span className="journey__section-number">02</span>
                </div>
                <div className="journey__activity-layout">
                  <div className="journey__activity-copy">
                    <span className="journey__metric-large">{personal?.high_risk_rate ?? 0}<small>%</small></span>
                    <strong>of your checks were high risk</strong>
                    <p>{personal?.activity_insight || 'Keep checking messages here to reveal how your risk pattern changes over time.'}</p>
                    <div className="journey__activity-pills"><span>{personal?.total_checks ?? 0} total checks</span><span>{personal?.recent_high_risk_count ?? 0} high risk recently</span></div>
                  </div>
                  <TrendChart points={personal?.trend || []} emptyText="Your monthly activity will appear here after you check messages." />
                </div>
              </FocusScene>
            </Reveal>

            <Reveal className="journey__reveal--wide" delay={120}>
              <section className="journey__community">
                <div className="journey__section-heading">
                  <div><p className="journey__eyebrow">03 / Everyone using Verif-AI</p><h2>What is happening around you?</h2><p>Authenticated community checks reveal which patterns are appearing most often right now.</p></div>
                  <div className="journey__section-header-right">
                    <span className="journey__community-rate">{community?.scam_rate ?? 0}% flagged</span>
                    <span className="journey__section-number">03</span>
                  </div>
                </div>
                <p className="journey__community-summary">{community?.summary || 'Community trends are still being collected.'}</p>
                <div className="journey__community-compare">
                  <div><span>Your top pattern</span><strong>{personal?.most_common_type || 'Not enough data'}</strong></div>
                  <div className="journey__compare-arrow" aria-hidden="true">↔</div>
                  <div><span>Community top pattern</span><strong>{community?.most_common_type || 'Not enough data'}</strong></div>
                </div>
                <AdviceCarousel community={community} />
                <div className="journey__community-grid">
                  <BarChart items={community?.top_types || []} emptyText="Community trends will appear as more checks are made." />
                  <TrendChart points={community?.trend || []} emptyText="Community activity will appear here soon." />
                </div>
              </section>
            </Reveal>
          </>
        )}
      </main>
    </div>
  );
}
