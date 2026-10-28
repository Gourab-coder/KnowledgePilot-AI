import { Brand } from "./Brand.jsx";
import { Icon } from "./Icon.jsx";

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function DocumentList({ documents, selectedIds, onToggle, onDelete }) {
  if (!documents.length) {
    return <p className="sidebar-empty">Add a PDF to start building your library.</p>;
  }

  return documents.map((document) => (
    <div className="document-row" key={document.id}>
      <label className="document-select" title={`Include ${document.filename} in chat`}>
        <input
          type="checkbox"
          checked={selectedIds.includes(document.id)}
          onChange={() => onToggle(document.id)}
        />
        <span className="checkbox-custom">
          <Icon name="check" size={12} />
        </span>
        <span className="file-icon">
          <Icon name="file" size={16} />
        </span>
        <span className="document-name" title={document.filename}>
          {document.filename}
        </span>
      </label>
      <button
        type="button"
        className="icon-button delete-document"
        aria-label={`Delete ${document.filename}`}
        title="Delete document"
        onClick={() => onDelete(document)}
      >
        <Icon name="trash" size={15} />
      </button>
    </div>
  ));
}

function ConversationList({ conversations, activeId, onOpen }) {
  if (!conversations.length) {
    return <p className="sidebar-empty">Your chats will show up here.</p>;
  }

  return conversations.map((conversation) => (
    <button
      type="button"
      key={conversation.id}
      className={`conversation-link ${activeId === conversation.id ? "active" : ""}`}
      onClick={() => onOpen(conversation.id)}
    >
      <Icon name="message" size={16} />
      <span>Chat · {formatDate(conversation.updated_at)}</span>
    </button>
  ));
}

export function Sidebar({
  user,
  documents,
  selectedIds,
  conversations,
  activeConversationId,
  uploading,
  onAddDocument,
  onNewChat,
  onToggleDocument,
  onDeleteDocument,
  onOpenConversation,
  onSignOut,
}) {
  const firstName = user.email.split("@")[0];

  return (
    <aside className="sidebar">
      <Brand className="sidebar-brand" />

      <button className="new-chat-button" type="button" onClick={onNewChat}>
        <Icon name="plus" size={18} />
        New conversation
      </button>

      <section className="sidebar-section document-section">
        <div className="section-heading">
          <span>Your library</span>
          <span className="count-pill">{documents.length}</span>
        </div>
        <div className="document-list">
          <DocumentList
            documents={documents}
            selectedIds={selectedIds}
            onToggle={onToggleDocument}
            onDelete={onDeleteDocument}
          />
        </div>
        <button
          type="button"
          className="add-document-button"
          onClick={onAddDocument}
          disabled={uploading}
        >
          <Icon name="plus" size={16} />
          {uploading ? "Adding PDF…" : "Add a PDF"}
        </button>
      </section>

      <section className="sidebar-section history-section">
        <div className="section-heading">
          <span>Recent conversations</span>
        </div>
        <div className="conversation-list">
          <ConversationList
            conversations={conversations}
            activeId={activeConversationId}
            onOpen={onOpenConversation}
          />
        </div>
      </section>

      <div className="sidebar-footer">
        <div className="user-avatar">{firstName.slice(0, 1).toUpperCase()}</div>
        <div className="user-details">
          <span className="user-name">{firstName}</span>
          <span className="user-email">{user.email}</span>
        </div>
        <button
          className="icon-button logout-button"
          type="button"
          onClick={onSignOut}
          title="Sign out"
          aria-label="Sign out"
        >
          <Icon name="logout" size={17} />
        </button>
      </div>
    </aside>
  );
}
