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
        <div className="analytics-recent__header">
          <h4>Recent Visits</h4>
        </div>
        <p className="analytics-recent__empty">No recent visits recorded yet</p>
      </div>
    );
  }

  return (
    <div className="analytics-recent">
      <div className="analytics-recent__header">
        <h4>Recent Visits</h4>
        <span className="analytics-recent__live-badge">● Live</span>
      </div>
      <div className="analytics-recent__list">
        {data.slice(0, 10).map((visit, index) => {
          const isAuth = visit.is_authenticated || visit.authenticated;
          return (
            <div key={index} className="analytics-recent__item">
              <div className="analytics-recent__path-group">
                <span
                  className={`analytics-recent__auth-dot analytics-recent__auth-dot--${isAuth ? 'auth' : 'anon'}`}
                  title={isAuth ? 'Authenticated' : 'Anonymous'}
                />
                <span className="analytics-recent__path">{visit.path}</span>
              </div>
              <span className="analytics-recent__device">{visit.device_type || 'unknown'}</span>
              <span className="analytics-recent__time">{formatTimeAgo(visit.timestamp)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

RecentVisits.propTypes = {
  data: PropTypes.array,
};
