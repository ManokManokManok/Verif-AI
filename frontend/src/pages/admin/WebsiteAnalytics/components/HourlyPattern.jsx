/**
 * HourlyPattern Component
 *
 * Displays 24-hour traffic pattern visualization.
 */

import React from 'react';
import PropTypes from 'prop-types';

const X_AXIS_LABELS = [
  { hour: 0,  label: '12am' },
  { hour: 6,  label: '6am'  },
  { hour: 12, label: '12pm' },
  { hour: 18, label: '6pm'  },
  { hour: 23, label: '11pm' },
];

export default function HourlyPattern({ data }) {
  const [hoveredHour, setHoveredHour] = React.useState(null);

  if (!data) return null;

  const hours = Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    label: i === 0 ? '12am' : i < 12 ? `${i}am` : i === 12 ? '12pm' : `${i - 12}pm`,
    value: data[i] || 0,
  }));

  const maxValue = Math.max(...hours.map(h => h.value), 1);
  const peakHour = hours.reduce((best, h) => (h.value > best.value ? h : best), hours[0]);

  // Y-axis grid lines at 25%, 50%, 75%, 100%
  const gridLines = [0.25, 0.5, 0.75, 1].map(pct => ({
    pct,
    label: Math.round(maxValue * pct),
  }));

  const hovered = hoveredHour !== null ? hours[hoveredHour] : null;

  return (
    <div className="analytics-hourly">
      <div className="analytics-hourly__header">
        <h4>Hourly Traffic Pattern</h4>
        {peakHour.value > 0 && (
          <span className="analytics-hourly__peak">
            Peak: {peakHour.label} ({peakHour.value})
          </span>
        )}
      </div>

      <div className="analytics-hourly__chart-wrap">
        {/* Y-axis labels */}
        <div className="analytics-hourly__y-axis">
          {[...gridLines].reverse().map(({ pct, label }) => (
            <span key={pct} className="analytics-hourly__y-label">{label}</span>
          ))}
        </div>

        {/* Plot area */}
        <div className="analytics-hourly__plot">
          {/* Grid lines */}
          <div className="analytics-hourly__grid">
            {gridLines.map(({ pct }) => (
              <div
                key={pct}
                className="analytics-hourly__gridline"
                style={{ bottom: `${pct * 100}%` }}
              />
            ))}
          </div>

          {/* Bars */}
          <div className="analytics-hourly__bars">
            {hours.map((hour) => {
              const heightPct = (hour.value / maxValue) * 100;
              const isPeak = hour.hour === peakHour.hour && peakHour.value > 0;
              const isHovered = hoveredHour === hour.hour;
              // intensity 0–1 for colour blending
              const intensity = hour.value / maxValue;

              return (
                <div
                  key={hour.hour}
                  className="analytics-hourly__col"
                  onMouseEnter={() => setHoveredHour(hour.hour)}
                  onMouseLeave={() => setHoveredHour(null)}
                >
                  {isHovered && hour.value > 0 && (
                    <div className={`analytics-hourly__tooltip${hour.hour > 18 ? ' analytics-hourly__tooltip--left' : ''}`}>
                      <strong>{hour.label}</strong>
                      <span>{hour.value} visit{hour.value !== 1 ? 's' : ''}</span>
                    </div>
                  )}
                  <div className="analytics-hourly__bar-track">
                    <div
                      className={`analytics-hourly__bar${isPeak ? ' analytics-hourly__bar--peak' : ''}${isHovered ? ' analytics-hourly__bar--hovered' : ''}`}
                      style={{
                        height: `${heightPct}%`,
                        opacity: hour.value === 0 ? 0.15 : 0.55 + intensity * 0.45,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* X-axis */}
          <div className="analytics-hourly__x-axis">
            {X_AXIS_LABELS.map(({ hour, label }) => (
              <span
                key={hour}
                className="analytics-hourly__x-label"
                style={{ left: `${(hour / 23) * 100}%` }}
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Hover summary strip */}
      {hovered && (
        <div className="analytics-hourly__summary">
          <span className="analytics-hourly__summary-hour">{hovered.label}</span>
          <span className="analytics-hourly__summary-visits">{hovered.value} visit{hovered.value !== 1 ? 's' : ''}</span>
          {hovered.value > 0 && (
            <span className="analytics-hourly__summary-pct">
              {((hovered.value / maxValue) * 100).toFixed(0)}% of peak
            </span>
          )}
        </div>
      )}
    </div>
  );
}

HourlyPattern.propTypes = {
  data: PropTypes.object,
};
