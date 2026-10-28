import { Icon } from "./Icon.jsx";

const suggestedQuestions = [
  "What are the key points?",
  "Summarize this document",
  "Find important dates",
];

export function WelcomePanel({ firstName, documentCount, selectedCount, onAddDocument, onSuggest }) {
  return (
    <div className="welcome-panel">
      <div className="welcome-icon">
        <Icon name="sparkles" size={28} />
      </div>
      <p className="eyebrow">A LITTLE LESS SEARCHING, A LOT MORE KNOWING</p>
      <h1>Good to see you, {firstName}.</h1>
      <p className="welcome-copy">
        Ask a question about your documents. I’ll find the relevant passages
        and show you exactly where the answer came from.
      </p>

      {documentCount === 0 ? (
        <button className="upload-prompt" type="button" onClick={onAddDocument}>
          <span className="upload-prompt-icon">
            <Icon name="upload" size={20} />
          </span>
          <span>
            <strong>Start with a PDF</strong>
            <small>Choose a file or drag it anywhere into this window</small>
          </span>
          <Icon name="chevron" size={18} />
        </button>
      ) : (
        <>
          <div className="suggestion-grid">
            {suggestedQuestions.map((question) => (
              <button
                className="suggestion"
                key={question}
                type="button"
                onClick={() => onSuggest(question)}
              >
                <Icon name="sparkles" size={15} />
                {question}
              </button>
            ))}
          </div>
          <p className="library-note">
            <Icon name="file" size={14} />
            {selectedCount || "All"} document{selectedCount === 1 ? "" : "s"} in your workspace
          </p>
        </>
      )}
    </div>
  );
}
