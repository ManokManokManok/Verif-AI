import PropTypes from 'prop-types';

export default function DetectionSidebarFrame({ children, isOpen, onToggle, variant = '' }) {
  const className = [
    'detect__sidebar',
    variant && `detect__sidebar--${variant}`,
    isOpen && 'detect__sidebar--open',
  ].filter(Boolean).join(' ');

  return (
    <aside className={className} style={{ width: isOpen ? 320 : 72 }}>
      <button
        className="detect__sidebtn detect__sidebtn--menu"
        type="button"
        aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
        aria-expanded={isOpen}
        onClick={onToggle}
      >
        {isOpen ? '✕' : '☰'}
      </button>
      {children}
    </aside>
  );
}

DetectionSidebarFrame.propTypes = {
  children: PropTypes.node.isRequired,
  isOpen: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
  variant: PropTypes.string,
};
