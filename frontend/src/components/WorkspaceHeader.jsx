import { Icon } from "./Icon.jsx";

export function WorkspaceHeader({ onSignOut }) {
  return (
    <header className="topbar">
      <div className="topbar-label">
        <span className="status-dot" />
        DOCUMENT ASSISTANT
      </div>
      <div className="topbar-right">
        <span className="private-label">
          <Icon name="check" size={14} />
          Private workspace
        </span>
        <button type="button" className="mobile-signout" onClick={onSignOut}>
          Sign out
        </button>
      </div>
    </header>
  );
}
