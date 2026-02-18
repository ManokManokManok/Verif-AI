/**
 * RecentVisits Component
 * 
 * Live feed of recent website visits.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { formatTimeAgo } from '../utils';

export default function RecentVisits({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="analytics-recent">
        <h4>Recent Visits</h4>
        <p className="analytics-recent__empty">No recent visits</p>
      </div>
    );
  }

  return (
    <div className="analytics-recent">
      <h4>Recent Visits (Live)</h4>
      <div className="analytics-recent__list">
        {data.slice(0, 10).map((visit, index) => (
          <div key={index} className="analytics-recent__item">
            <span className="analytics-recent__path">{visit.path}</span>
            <span className="analytics-recent__device">{visit.device_type || 'unknown'}</span>
            <span className="analytics-recent__time">
              {formatTimeAgo(visit.timestamp)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

RecentVisits.propTypes = {
  data: PropTypes.array,
};
