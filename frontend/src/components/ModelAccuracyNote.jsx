import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { getModelInfoRequest } from '../api/client';
import './ModelAccuracyNote.css';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export function formatDatasetUpdated(month, now = new Date()) {
  const match = /^(\d{4})-(\d{2})$/.exec(month || '');
  if (!match) return null;
  const year = Number(match[1]);
  const monthIndex = Number(match[2]) - 1;
  const label = `${MONTH_NAMES[monthIndex]} ${year}`;
  const diff = (now.getFullYear() - year) * 12 + (now.getMonth() - monthIndex);
  let ago = 'this month';
  if (diff === 1) ago = '1 month ago';
  else if (diff > 1 && diff < 12) ago = `${diff} months ago`;
  else if (diff >= 12) {
    const years = Math.floor(diff / 12);
    ago = `${years} year${years > 1 ? 's' : ''} ago`;
  }
  return { label, ago };
}

export default function ModelAccuracyNote({ className = '' }) {
  const [info, setInfo] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [infoOpen, setInfoOpen] = useState(false);
  const wrapperRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    getModelInfoRequest()
      .then((res) => {
        if (!cancelled) setInfo(res?.data || null);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!expanded) setInfoOpen(false);
  }, [expanded]);

  useEffect(() => {
    if (!infoOpen) return undefined;
    const onPointerDown = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) setInfoOpen(false);
    };
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setInfoOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [infoOpen]);

  const accuracy = info?.accuracy;
  const updated = formatDatasetUpdated(info?.dataset_updated);
  if (!accuracy && !updated) return null;

  return (
    <div className={`modelNote ${expanded ? 'modelNote--open' : ''} ${className}`} ref={wrapperRef}>
      <button
        type="button"
        className="modelNote__toggle"
        aria-expanded={expanded}
        aria-controls="modelNotePanel"
        onClick={() => setExpanded((value) => !value)}
      >
        <span>
          {updated
            ? `Dataset was last updated ${updated.label} (${updated.ago})`
            : 'About this result'}
        </span>
        <svg className="modelNote__chevron" width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      <div className="modelNote__panel" id="modelNotePanel" aria-hidden={!expanded}>
        <div className="modelNote__panelInner">
          <div className="modelNote__body">
            {accuracy && (
              <p className="modelNote__text">
                In testing on a split of our dataset, Verif-AI was right about{' '}
                <strong>{accuracy.accuracy}%</strong> of the time, with a margin of error of about{' '}
                <strong>±{accuracy.margin_of_error.toFixed(1)}%</strong>. Results on real messages
                may vary.
              </p>
            )}
            <button
              type="button"
              className="modelNote__info"
              aria-label="More about accuracy and margin of error"
              aria-expanded={infoOpen}
              tabIndex={expanded ? 0 : -1}
              onClick={() => setInfoOpen((value) => !value)}
            >
              i
            </button>
          </div>
          {infoOpen && (
            <div className="modelNote__popover" role="note">
              <p>
                This figure comes from testing the model on part of our own dataset. The margin of
                error shows how far the real accuracy could be above or below that number.
              </p>
              <p>
                Your result can differ. Accuracy depends on the wording, length, language and type
                of the message you submit, and on new scam tactics that are not in our dataset yet.
              </p>
              <p>
                Treat this as a guide, not a guarantee. If a message feels suspicious, verify it
                through an official channel before acting on it.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

ModelAccuracyNote.propTypes = {
  className: PropTypes.string,
};
