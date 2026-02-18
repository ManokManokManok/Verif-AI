/**
 * SearchInput Component
 * 
 * Search input with debounce support.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './SearchInput.css';

export default function SearchInput({ 
  value, 
  onChange, 
  placeholder = 'Search...', 
  debounce = 300,
  className = '' 
}) {
  const [localValue, setLocalValue] = React.useState(value);
  const timeoutRef = React.useRef(null);

  React.useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = (e) => {
    const newValue = e.target.value;
    setLocalValue(newValue);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      onChange(newValue);
    }, debounce);
  };

  return (
    <div className={`search-input ${className}`}>
      <span className="search-input__icon">🔍</span>
      <input
        type="text"
        className="search-input__field"
        placeholder={placeholder}
        value={localValue}
        onChange={handleChange}
      />
      {localValue && (
        <button
          className="search-input__clear"
          onClick={() => { setLocalValue(''); onChange(''); }}
          aria-label="Clear search"
        >
          ✕
        </button>
      )}
    </div>
  );
}

SearchInput.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  placeholder: PropTypes.string,
  debounce: PropTypes.number,
  className: PropTypes.string,
};
