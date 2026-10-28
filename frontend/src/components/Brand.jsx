import { Icon } from "./Icon.jsx";

export function Brand({ className = "" }) {
  return (
    <a className={`brand ${className}`} href="/" aria-label="KnowledgePilot home">
      <span className="brand-mark">
        <Icon name="sparkles" size={21} />
      </span>
      <span>
        knowledge<span className="brand-accent">pilot</span>
      </span>
    </a>
  );
}
