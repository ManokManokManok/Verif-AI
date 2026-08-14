/**
 * DailyActivityChart Component
 *
 * Displays daily activity chart with total and scam detection bars.
 * Design follows HourlyPattern: absolute plot layout, gradient bars,
 * peak-day highlight, intensity opacity, and a hover summary strip.
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';

function formatDateLabel(dateStr) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

// Y-axis: 4 gridlines at 25 / 50 / 75 / 100 %
const GRID_PCTS = [0.25, 0.5, 0.75, 1];

export default function DailyActivityChart({ dailyCounts }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!dailyCounts || dailyCounts.length === 0) {
    return (
      <div className="admin-card">
        <div className="admin-card__header">
          <h3 className="admin-card__title">Daily Activity</h3>
        </div>
        <div className="analysis-stats__chart-empty">
          <p>📊 No activity data available for the selected period</p>
          <p className="analysis-stats__chart-hint">
            Data will appear as analyses are performed
          </p>
        </div>
      </div>
    );
  }

  const displayData = dailyCounts.slice(-14);
  const maxCount = Math.max(...displayData.map(d => d.total || 0), 1);
  const peakIdx = displayData.reduce(
    (best, d, i) => (d.total || 0) > (displayData[best].total || 0) ? i : best,
    0
  );
  const dateRange = displayData.length > 1
    ? `${formatDateLabel(displayData[0].date)} – ${formatDateLabel(displayData[displayData.length - 1].date)}`
    : displayData.length === 1 ? formatDateLabel(displayData[0].date) : '';

  const gridLines = GRID_PCTS.map(pct => ({
    pct,
    label: Math.round(maxCount * pct),
  }));

  const hovered = hoveredIdx !== null ? displayData[hoveredIdx] : null;
  const lastFewThreshold = Math.floor(displayData.length * 0.7);

  return (
    <div className="admin-card">
      <div className="admin-card__header">
        <h3 className="admin-card__title">Daily Activity</h3>
        <div className="daily-chart__header-meta">
          {dateRange && <span className="analysis-stats__card-subtitle">{dateRange}</span>}
          {maxCount > 0 && (
            <span className="daily-chart__peak-badge">
              Peak: {formatDateLabel(displayData[peakIdx].date)} ({displayData[peakIdx].total})
            </span>
          )}
        </div>
      </div>

      <div className="daily-chart">
        {/* Y-axis + plot */}
        <div className="daily-chart__wrap">
          {/* Y-axis labels */}
          <div className="daily-chart__y-axis">
            {[...gridLines].reverse().map(({ pct, label }) => (
              <span key={pct} className="daily-chart__y-label">{label}</span>
            ))}
          </div>

          {/* Plot area */}
          <div className="daily-chart__plot">
            {/* Grid lines */}
            <div className="daily-chart__grid">
              {gridLines.map(({ pct }) => (
                <div
                  key={pct}
                  className="daily-chart__gridline"
                  style={{ bottom: `${pct * 100}%` }}
                />
              ))}
            </div>

            {/* Bars */}
            <div className="daily-chart__bars">
              {displayData.map((day, idx) => {
                const total = day.total || 0;
                const scams = day.scams || 0;
                const heightPct = (total / maxCount) * 100;
                const scamHeightPct = total > 0 ? (scams / total) * 100 : 0;
                const isPeak = idx === peakIdx && total > 0;
                const isHovered = hoveredIdx === idx;
                const intensity = total / maxCount;
                const isRight = idx >= lastFewThreshold;

                return (
                  <div
                    key={idx}
                    className="daily-chart__col"
                    onMouseEnter={() => setHoveredIdx(idx)}
                    onMouseLeave={() => setHoveredIdx(null)}
                  >
                    {isHovered && total > 0 && (
                      <div className={`daily-chart__tooltip${isRight ? ' daily-chart__tooltip--left' : ''}`}>
                        <strong>{formatDateLabel(day.date)}</strong>
                        <span>{total} total</span>
                        <span className="daily-chart__tooltip-scam">
                          {scams} scam{scams !== 1 ? 's' : ''} ({total > 0 ? ((scams / total) * 100).toFixed(0) : 0}%)
                        </span>
                      </div>
                    )}
                    <div className="daily-chart__bar-track">
                      <div
                        className={`daily-chart__bar${isPeak ? ' daily-chart__bar--peak' : ''}${isHovered ? ' daily-chart__bar--hovered' : ''}`}
                        style={{
                          height: `${heightPct}%`,
                          opacity: total === 0 ? 0.15 : 0.55 + intensity * 0.45,
                        }}
                      >
                        {scamHeightPct > 0 && (
                          <div
                            className="daily-chart__bar-scam"
                            style={{ height: `${scamHeightPct}%` }}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* X-axis */}
            <div className="daily-chart__x-axis">
              {displayData.map((day, idx) => (
                <span key={idx} className="daily-chart__x-label">
                  {new Date(day.date).getDate()}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Hover summary strip */}
        <div className={`daily-chart__summary${hovered ? ' daily-chart__summary--visible' : ''}`}>
          {hovered ? (
            <>
              <span className="daily-chart__summary-date">{formatDateLabel(hovered.date)}</span>
              <span className="daily-chart__summary-total">{hovered.total || 0} analyses</span>
              <span className="daily-chart__summary-scam">
                {hovered.scams || 0} scam{(hovered.scams || 0) !== 1 ? 's' : ''}
              </span>
              {(hovered.total || 0) > 0 && (
                <span className="daily-chart__summary-pct">
                  {(((hovered.scams || 0) / hovered.total) * 100).toFixed(0)}% detection rate
                </span>
              )}
            </>
          ) : (
            <span className="daily-chart__summary-hint">Hover over a bar for details</span>
          )}
        </div>

        {/* Legend */}
        <div className="analysis-stats__chart-legend">
          <span className="analysis-stats__legend-item">
            <span className="analysis-stats__legend-color analysis-stats__legend-color--total" />
            Total Analyses
          </span>
          <span className="analysis-stats__legend-item">
            <span className="analysis-stats__legend-color analysis-stats__legend-color--scam" />
            Scams Detected
          </span>
        </div>
      </div>
    </div>
  );
}

DailyActivityChart.propTypes = {
  dailyCounts: PropTypes.arrayOf(PropTypes.shape({
    date: PropTypes.string.isRequired,
    total: PropTypes.number,
    scams: PropTypes.number,
  })),
};
