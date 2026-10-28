import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Icon } from "./Icon.jsx";

function CitationCard({ citation }) {
  return (
    <div className="citation-card">
      <div className="citation-heading">
        <span className="citation-file">
          <Icon name="file" size={14} />
          {citation.filename}
        </span>
        <span className="citation-page">Page {citation.page_number}</span>
      </div>
      <p>“{citation.excerpt}”</p>
    </div>
  );
}

function Message({ message, firstName }) {
  const isAssistant = message.role === "assistant";
  const citations = message.citations ?? [];

  return (
    <article className={`message message-${message.role}`}>
      <div className="message-avatar">
        {isAssistant ? (
          <Icon name="sparkles" size={17} />
        ) : (
          firstName.slice(0, 1).toUpperCase()
        )}
      </div>
      <div className="message-body">
        <div className="message-meta">
          <strong>{isAssistant ? "KnowledgePilot" : "You"}</strong>
          {isAssistant && citations.length > 0 && (
            <span className="source-count">
              <Icon name="book" size={13} />
              {citations.length} source{citations.length === 1 ? "" : "s"}
            </span>
          )}
        </div>
        <div className={`message-content ${isAssistant ? "markdown-content" : ""}`}>
          {isAssistant ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          ) : (
            message.content
          )}
        </div>
        {isAssistant && citations.length > 0 && (
          <div className="citation-list">
            {citations.map((citation) => (
              <CitationCard citation={citation} key={citation.chunk_id} />
            ))}
          </div>
        )}
      </div>
    </article>
  );
}

function ThinkingIndicator() {
  return (
    <div className="message message-assistant">
      <div className="message-avatar">
        <Icon name="sparkles" size={17} />
      </div>
      <div className="message-body">
        <div className="message-meta">
          <strong>KnowledgePilot</strong>
        </div>
        <div className="typing-indicator">
          <i />
          <i />
          <i />
          <span>Looking through your documents…</span>
        </div>
      </div>
    </div>
  );
}

export function MessageList({ messages, firstName, sending, loading }) {
  return (
    <div className="message-list" aria-live="polite">
      {loading && <div className="conversation-loading">Loading conversation…</div>}
      {messages.map((message) => (
        <Message key={message.id} message={message} firstName={firstName} />
      ))}
      {sending && <ThinkingIndicator />}
    </div>
  );
}
