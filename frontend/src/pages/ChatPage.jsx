import { useEffect, useRef, useState } from "react";

import { ChatComposer } from "../components/ChatComposer.jsx";
import { Icon } from "../components/Icon.jsx";
import { MessageList } from "../components/MessageList.jsx";
import { Notification } from "../components/Notification.jsx";
import { Sidebar } from "../components/Sidebar.jsx";
import { WelcomePanel } from "../components/WelcomePanel.jsx";
import { WorkspaceHeader } from "../components/WorkspaceHeader.jsx";
import { api } from "../services/api.js";

const MAX_UPLOAD_SIZE = 10 * 1024 * 1024;

export function ChatPage({ session, onSignOut }) {
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [notice, setNotice] = useState("");
  const fileInput = useRef(null);
  const scrollAnchor = useRef(null);
  const firstName = session.user.email.split("@")[0];

  useEffect(() => {
    let active = true;

    async function loadWorkspace() {
      try {
        const [loadedDocuments, loadedConversations] = await Promise.all([
          api.documents(session.token),
          api.conversations(session.token),
        ]);
        if (!active) return;
        setDocuments(loadedDocuments);
        setSelectedIds(loadedDocuments.map((document) => document.id));
        setConversations(loadedConversations);
      } catch (error) {
        if (active) setNotice(error.message);
      }
    }

    loadWorkspace();
    return () => {
      active = false;
    };
  }, [session.token]);

  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  function openFilePicker() {
    fileInput.current?.click();
  }

  async function uploadFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setNotice("Please choose a PDF file.");
      return;
    }
    if (file.size > MAX_UPLOAD_SIZE) {
      setNotice("This PDF is larger than the 10 MB upload limit.");
      return;
    }

    setUploading(true);
    setNotice("");
    try {
      const document = await api.uploadDocument(file, session.token);
      setDocuments((currentDocuments) => [document, ...currentDocuments]);
      setSelectedIds((currentIds) => [...new Set([...currentIds, document.id])]);
      setNotice(`“${document.filename}” is ready to chat with.`);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  function handleFileSelection(event) {
    uploadFile(event.target.files?.[0]);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    uploadFile(event.dataTransfer.files?.[0]);
  }

  function toggleDocument(documentId) {
    setSelectedIds((currentIds) =>
      currentIds.includes(documentId)
        ? currentIds.filter((id) => id !== documentId)
        : [...currentIds, documentId],
    );
  }

  async function deleteDocument(document) {
    if (!window.confirm(`Delete “${document.filename}” and its indexed content?`)) return;

    try {
      await api.deleteDocument(document.id, session.token);
      setDocuments((currentDocuments) =>
        currentDocuments.filter((item) => item.id !== document.id),
      );
      setSelectedIds((currentIds) => currentIds.filter((id) => id !== document.id));
      setNotice(`“${document.filename}” was deleted.`);
    } catch (error) {
      setNotice(error.message);
    }
  }

  function startNewChat() {
    setConversationId(null);
    setMessages([]);
    setQuestion("");
    setNotice("");
  }

  async function openConversation(id) {
    setConversationId(id);
    setMessages([]);
    setLoadingMessages(true);
    setNotice("");

    try {
      setMessages(await api.messages(id, session.token));
    } catch (error) {
      setNotice(error.message);
    } finally {
      setLoadingMessages(false);
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    const text = question.trim();
    if (!text || sending) return;

    setQuestion("");
    setMessages((currentMessages) => [
      ...currentMessages,
      { id: `pending-${Date.now()}`, role: "user", content: text, citations: [] },
    ]);
    setSending(true);
    setNotice("");

    try {
      const result = await api.chat(
        {
          question: text,
          conversation_id: conversationId,
          document_ids: selectedIds,
        },
        session.token,
      );
      setConversationId(result.conversation_id);
      setMessages((currentMessages) => [
        ...currentMessages.filter((message) => !message.id.startsWith("pending-")),
        { id: `user-${Date.now()}`, role: "user", content: text, citations: [] },
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: result.answer,
          citations: result.citations,
        },
      ]);
      setConversations((currentConversations) => [
        {
          id: result.conversation_id,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        ...currentConversations.filter((item) => item.id !== result.conversation_id),
      ]);
    } catch (error) {
      setMessages((currentMessages) =>
        currentMessages.filter((message) => !message.id.startsWith("pending-")),
      );
      setQuestion(text);
      setNotice(error.message);
    } finally {
      setSending(false);
    }
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="app-shell">
      <Sidebar
        user={session.user}
        documents={documents}
        selectedIds={selectedIds}
        conversations={conversations}
        activeConversationId={conversationId}
        uploading={uploading}
        onAddDocument={openFilePicker}
        onNewChat={startNewChat}
        onToggleDocument={toggleDocument}
        onDeleteDocument={deleteDocument}
        onOpenConversation={openConversation}
        onSignOut={onSignOut}
      />

      <main className="workspace">
        <WorkspaceHeader onSignOut={onSignOut} />

        <section
          className={`chat-area ${hasMessages ? "" : "chat-area-empty"}`}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false);
          }}
          onDrop={handleDrop}
        >
          {dragging && (
            <div className="drop-overlay">
              <Icon name="upload" size={29} />
              <span>Drop your PDF to add it</span>
            </div>
          )}

          <Notification message={notice} onDismiss={() => setNotice("")} />

          {!hasMessages && !loadingMessages ? (
            <WelcomePanel
              firstName={firstName}
              documentCount={documents.length}
              selectedCount={selectedIds.length}
              onAddDocument={openFilePicker}
              onSuggest={setQuestion}
            />
          ) : (
            <MessageList
              messages={messages}
              firstName={firstName}
              sending={sending}
              loading={loadingMessages}
            />
          )}
          <div ref={scrollAnchor} />
        </section>

        <ChatComposer
          question={question}
          documentCount={documents.length}
          selectedCount={selectedIds.length}
          sending={sending}
          onQuestionChange={setQuestion}
          onSend={sendMessage}
          onAddDocument={openFilePicker}
        />

        <input
          ref={fileInput}
          className="visually-hidden"
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileSelection}
          aria-label="Choose a PDF to upload"
        />
      </main>
    </div>
  );
}
