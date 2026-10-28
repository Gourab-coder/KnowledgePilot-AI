import { Icon } from "./Icon.jsx";

export function ChatComposer({
  question,
  documentCount,
  selectedCount,
  sending,
  onQuestionChange,
  onSend,
  onAddDocument,
}) {
  return (
    <footer className="composer-wrap">
      {documentCount > 0 && (
        <div className="composer-context">
          <span className="context-indicator" />
          {selectedCount === 0
            ? `Searching all ${documentCount} documents`
            : `${selectedCount} of ${documentCount} document${selectedCount === 1 ? "" : "s"} selected`}
          <button type="button" className="context-manage" onClick={onAddDocument}>
            Add PDF
          </button>
        </div>
      )}

      <form className="composer" onSubmit={onSend}>
        <textarea
          aria-label="Ask a question about your documents"
          placeholder={
            documentCount
              ? "Ask anything about your documents…"
              : "Add a PDF to start a conversation…"
          }
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form.requestSubmit();
            }
          }}
          maxLength={4000}
          rows={1}
        />
        <button
          className="send-button"
          type="submit"
          disabled={!question.trim() || sending || documentCount === 0}
          aria-label="Send question"
          title="Send question"
        >
          <Icon name="arrow" size={19} />
        </button>
      </form>
      <p className="composer-footnote">
        Answers are based on your documents. Always verify important details against the source.
      </p>
    </footer>
  );
}
