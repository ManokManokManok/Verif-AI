import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Analytics.css';
import { useAuth } from '../context/AuthContext';
import { getUserSafetySummary, getGlobalSafetySummary } from '../api/analytics';

function BarChart({ items, emptyText }) {
  if (!items.length) return <p className="journey__empty">{emptyText}</p>;

  const maxCount = Math.max(...items.map((item) => item.count), 1);
  return (
    <div className="journey__bars" aria-label="Scam types chart">
      {items.map((item) => (
        <div className="journey__bar-row" key={item.type}>
          <div className="journey__bar-label">
            <span title={item.type}>{item.type}</span>
            <strong>{item.count}</strong>
          </div>
          <div className="journey__bar-track">
            <span style={{ width: `${Math.max((item.count / maxCount) * 100, 4)}%` }} />
          </div>
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
            <span style={{ height: `${Math.max((point.count / maxCount) * 100, 8)}%` }} />
          </div>
          <span className="journey__trend-label">{point.label}</span>
        </div>
      ))}
    </div>
  );
}

const SCAM_GUIDANCE = {
  'Banking Access & Payment': {
    action: 'They may pretend to be your bank and try to make you share a password, one-time code, or card details.',
    advice: 'Contact your bank through its official app or the number on your card. Do not use links in the message.',
  },
  'Financial and Investment': {
    action: 'They may promise guaranteed profits or pressure you to transfer money before you have time to check the offer.',
    advice: 'Do not send money based on a promise. Look up the company independently and discuss it with someone you trust.',
  },
  'Health and Wellness': {
    action: 'They may offer a miracle treatment or ask for payment and personal health details urgently.',
    advice: 'Speak with a trusted medical professional and use the clinic or service\'s official contact details.',
  },
  'Impersonation and Authority': {
    action: 'They may pretend to be a government office, police officer, company, or someone you know.',
    advice: 'Pause and contact the real person or organization using contact details you find yourself.',
  },
  'Job, Business, and Work-from-Home': {
    action: 'They may offer easy money or a job, then ask for an upfront fee, personal documents, or bank details.',
    advice: 'Never pay to get a job. Verify the employer through its official website before sharing information.',
  },
  'Legal and Document': {
    action: 'They may threaten fines, legal trouble, or missed deadlines to make you pay or reveal personal information.',
    advice: 'Do not panic. Contact the organization directly through its official website or phone number.',
  },
  'Prize, Raffle & Reward': {
    action: 'They may say you won a prize and ask for a fee, bank details, or a link click to claim it.',
    advice: 'You cannot usually win a contest you never entered. Do not pay a fee to receive a prize.',
  },
  'Property & Rental': {
    action: 'They may advertise a property at an unusually low price and ask for a deposit before you see it.',
    advice: 'Visit the property and verify the owner or agent independently before sending any money.',
  },
  'Romance, Dating, and Relationship': {
    action: 'They may build trust and then create an emergency that requires money or gift cards.',
    advice: 'Never send money to someone you have not met and speak with someone you trust before acting.',
  },
  'Shopping and E-Commerce': {
    action: 'They may use a fake shop, an unbelievable discount, or a payment link to take your money or card details.',
    advice: 'Use a trusted store directly and choose a protected payment method. Be cautious with deals that feel rushed.',
  },
  'Tax, Banking, and Loan': {
    action: 'They may claim you owe money or offer a quick loan, then request an urgent payment or sensitive details.',
    advice: 'Check your account through the official tax, bank, or lender website. Do not pay because of a threatening message.',
  },
  'Tech and Online Account': {
    action: 'They may claim your account or device has a problem and ask for a code, password, or remote access.',
    advice: 'Close the message and open the official app or website yourself. Never share a one-time code.',
  },
  'Mobile and Digital': {
    action: 'They may send a link or code that is designed to take over your phone, account, or digital wallet.',
    advice: 'Do not open unexpected links or share security codes. Contact your provider through its official support channel.',
  },
};

function getGuidance(type) {
  return SCAM_GUIDANCE[type] || {
    action: 'They may use urgency, authority, or an attractive offer to make you act before you have time to verify the message.',
    advice: 'Pause, do not click or pay, and verify the request through an official contact method.',
  };
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
  const showPrevious = () => setSlide((current) => (current + 1) % 2);

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
            <p>{guidance.action}</p>
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
            <section className="journey__summary" aria-labelledby="safety-summary-title">
              <div className="journey__summary-icon" aria-hidden="true">✦</div>
              <div>
                <p className="journey__eyebrow">Your safety summary</p>
                <h2 id="safety-summary-title">{personal?.risk_level || 'No data yet'}</h2>
                <p>{personal?.summary || 'Check a message to start building your safety summary.'}</p>
              </div>
            </section>

            <section className="journey__stat-grid" aria-label="Your detection totals">
              <div className="journey__stat"><span>Messages checked</span><strong>{personal?.total_checks ?? 0}</strong></div>
              <div className="journey__stat journey__stat--alert"><span>High-risk results</span><strong>{personal?.high_risk_count ?? 0}</strong></div>
              <div className="journey__stat"><span>Most common pattern</span><strong>{personal?.most_common_type || 'Not enough data'}</strong></div>
            </section>

            <section className="journey__chart-grid">
              <div className="journey__panel">
                <div className="journey__panel-heading"><div><p className="journey__eyebrow">Your checks</p><h2>What you see most often</h2></div><span className="journey__panel-mark">01</span></div>
                <BarChart items={personal?.top_types || []} emptyText="Your scam patterns will appear here after you check messages." />
              </div>
              <div className="journey__panel">
                <div className="journey__panel-heading"><div><p className="journey__eyebrow">Your activity</p><h2>Checks over time</h2></div><span className="journey__panel-mark">02</span></div>
                <TrendChart points={personal?.trend || []} emptyText="Your monthly activity will appear here after you check messages." />
              </div>
            </section>

            <section className="journey__community">
              <div className="journey__panel-heading"><div><p className="journey__eyebrow">Everyone using Verif-AI</p><h2>Scam trends around the community</h2></div><span className="journey__community-rate">{community?.scam_rate ?? 0}% flagged</span></div>
              <p className="journey__community-summary">{community?.summary || 'Community trends are still being collected.'}</p>
              <AdviceCarousel community={community} />
              <div className="journey__community-grid">
                <BarChart items={community?.top_types || []} emptyText="Community trends will appear as more checks are made." />
                <TrendChart points={community?.trend || []} emptyText="Community activity will appear here soon." />
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
