import './LogoutOverlay.css';

// Full-screen blocker shown while logout is in flight so nothing can be clicked.
export default function LogoutOverlay() {
  return (
    <div className="logout-overlay" role="alertdialog" aria-live="assertive" aria-busy="true" aria-label="Logging out">
      <div className="logout-overlay__box">
        <div className="logout-overlay__spinner" />
        <p className="logout-overlay__text">Logging out...</p>
      </div>
    </div>
  );
}
