import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { getAdminModelInfo, updateDatasetUpdated } from '../../../../api/admin';

export default function DatasetUpdatedCard({ onNotify }) {
  const [saved, setSaved] = useState('');
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getAdminModelInfo()
      .then((res) => {
        const month = res?.data?.dataset_updated || '';
        setSaved(month);
        setValue(month);
      })
      .catch(() => onNotify?.('error', 'Failed to load dataset update date'));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await updateDatasetUpdated(value);
      const month = res?.data?.dataset_updated || value;
      setSaved(month);
      setValue(month);
      onNotify?.('success', 'Dataset update date saved. All users will now see it.');
    } catch (err) {
      onNotify?.('error', err?.message || 'Failed to save dataset update date');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="admin-card">
      <div className="admin-card__header">
        <h3 className="admin-card__title">Dataset Last Updated</h3>
      </div>
      <p className="admin-text-muted" style={{ fontSize: '0.8rem', margin: '0 0 0.75rem' }}>
        The month and year shown to all users as when the model was last updated or retrained.
      </p>
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          type="month"
          className="admin-input"
          value={value}
          min="2020-01"
          max="2100-12"
          onChange={(event) => setValue(event.target.value)}
          aria-label="Dataset last updated month"
        />
        <button
          type="button"
          className="admin-btn admin-btn--primary admin-btn--sm"
          onClick={handleSave}
          disabled={saving || !value || value === saved}
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </div>
  );
}

DatasetUpdatedCard.propTypes = {
  onNotify: PropTypes.func,
};
