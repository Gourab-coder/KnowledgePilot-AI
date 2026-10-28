import { Icon } from "./Icon.jsx";

export function Notification({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="notice" role="status">
      <span>{message}</span>
      <button
        type="button"
        className="icon-button"
        aria-label="Dismiss message"
        onClick={onDismiss}
      >
        <Icon name="close" size={16} />
      </button>
    </div>
  );
}
