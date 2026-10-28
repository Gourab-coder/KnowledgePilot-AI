import tempfile
import unittest
from pathlib import Path

import pymupdf
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.rag_service import RagService, UNCERTAINTY_ANSWER


class FakeEmbeddings:
    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        vector = [0.0] * 384
        vector[0] = 1.0
        return [vector.copy() for _ in texts]


class FakeGroq:
    def __init__(self):
        self.calls = 0

    def generate_grounded_answer(self, question: str, context: str) -> str:
        self.calls += 1
        return f"Grounded answer: {question}"


class BackendApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        settings = Settings(
            database_url="sqlite://",
            upload_dir=Path(self.temp_dir.name) / "uploads",
            jwt_secret_key="test-signing-key",
            chunk_size=300,
            chunk_overlap=30,
            retrieval_similarity_threshold=0.1,
        )
        self.app = create_app(settings)
        self.embeddings = FakeEmbeddings()
        self.groq = FakeGroq()
        self.app.state.embedding_service = self.embeddings
        self.app.state.rag_service = RagService(settings, self.embeddings, self.groq)
        self.client_context = TestClient(self.app)
        self.client = self.client_context.__enter__()
        self.user_token = self.register_and_login("reader@example.com")

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def register_and_login(self, email: str) -> str:
        registration = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "a-strong-test-password"},
        )
        self.assertEqual(registration.status_code, 201, registration.text)
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "a-strong-test-password"},
        )
        self.assertEqual(login.status_code, 200, login.text)
        return login.json()["access_token"]

    @staticmethod
    def authorization(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def make_pdf(text: str) -> bytes:
        document = pymupdf.open()
        page = document.new_page()
        page.insert_text((72, 72), text)
        content = document.tobytes()
        document.close()
        return content

    def upload_pdf(self, token: str, filename: str = "guide.pdf") -> dict[str, object]:
        response = self.client.post(
            "/api/v1/documents",
            headers=self.authorization(token),
            files={"file": (filename, self.make_pdf("Eligibility requires 18 months of residency."), "application/pdf")},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_registration_login_and_authentication(self) -> None:
        me = self.client.get("/api/v1/auth/me", headers=self.authorization(self.user_token))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], "reader@example.com")

        duplicate = self.client.post(
            "/api/v1/auth/register",
            json={"email": "READER@example.com", "password": "a-strong-test-password"},
        )
        self.assertEqual(duplicate.status_code, 409)

        unauthorized = self.client.get("/api/v1/documents")
        self.assertEqual(unauthorized.status_code, 401)

    def test_upload_list_and_get_document(self) -> None:
        uploaded = self.upload_pdf(self.user_token)
        self.assertEqual(uploaded["status"], "completed")
        self.assertEqual(uploaded["page_count"], 1)

        listed = self.client.get(
            "/api/v1/documents", headers=self.authorization(self.user_token)
        )
        self.assertEqual([document["id"] for document in listed.json()], [uploaded["id"]])

        retrieved = self.client.get(
            f"/api/v1/documents/{uploaded['id']}",
            headers=self.authorization(self.user_token),
        )
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(retrieved.json()["filename"], "guide.pdf")

    def test_chat_returns_retrieved_citations_and_persists_history(self) -> None:
        document = self.upload_pdf(self.user_token)
        response = self.client.post(
            "/api/v1/chat",
            headers=self.authorization(self.user_token),
            json={
                "question": "What is the residency requirement?",
                "document_ids": [document["id"]],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["answer"], "Grounded answer: What is the residency requirement?")
        self.assertEqual(result["citations"][0]["filename"], "guide.pdf")
        self.assertEqual(result["citations"][0]["page_number"], 1)
        self.assertIn("Eligibility requires", result["citations"][0]["excerpt"])

        messages = self.client.get(
            f"/api/v1/conversations/{result['conversation_id']}/messages",
            headers=self.authorization(self.user_token),
        )
        self.assertEqual(messages.status_code, 200)
        self.assertEqual([message["role"] for message in messages.json()], ["user", "assistant"])
        self.assertEqual(len(messages.json()[1]["citations"]), 1)

        conversations = self.client.get(
            "/api/v1/conversations", headers=self.authorization(self.user_token)
        )
        self.assertEqual(len(conversations.json()), 1)

    def test_user_cannot_access_another_users_documents_or_conversations(self) -> None:
        document = self.upload_pdf(self.user_token)
        first_user_chat = self.client.post(
            "/api/v1/chat",
            headers=self.authorization(self.user_token),
            json={"question": "What does this document say?", "document_ids": [document["id"]]},
        )
        self.assertEqual(first_user_chat.status_code, 200, first_user_chat.text)
        other_user_token = self.register_and_login("another@example.com")

        get_response = self.client.get(
            f"/api/v1/documents/{document['id']}",
            headers=self.authorization(other_user_token),
        )
        self.assertEqual(get_response.status_code, 404)

        chat_response = self.client.post(
            "/api/v1/chat",
            headers=self.authorization(other_user_token),
            json={"question": "Tell me about the document.", "document_ids": [document["id"]]},
        )
        self.assertEqual(chat_response.status_code, 404)

        delete_response = self.client.delete(
            f"/api/v1/documents/{document['id']}",
            headers=self.authorization(other_user_token),
        )
        self.assertEqual(delete_response.status_code, 404)

        messages_response = self.client.get(
            f"/api/v1/conversations/{first_user_chat.json()['conversation_id']}/messages",
            headers=self.authorization(other_user_token),
        )
        self.assertEqual(messages_response.status_code, 404)

        cross_user_chat = self.client.post(
            "/api/v1/chat",
            headers=self.authorization(other_user_token),
            json={
                "question": "Continue someone else's conversation.",
                "conversation_id": first_user_chat.json()["conversation_id"],
            },
        )
        self.assertEqual(cross_user_chat.status_code, 404)

    def test_invalid_upload_is_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/documents",
            headers=self.authorization(self.user_token),
            files={"file": ("not-a-pdf.pdf", b"not a pdf", "application/pdf")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/v1/documents", headers=self.authorization(self.user_token)).json(), [])

    def test_no_matching_documents_returns_uncertainty_without_calling_grok(self) -> None:
        response = self.client.post(
            "/api/v1/chat",
            headers=self.authorization(self.user_token),
            json={"question": "What is the answer?"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["answer"], UNCERTAINTY_ANSWER)
        self.assertEqual(response.json()["citations"], [])
        self.assertEqual(self.groq.calls, 0)

    def test_delete_document_removes_file_and_database_rows(self) -> None:
        document = self.upload_pdf(self.user_token)
        saved_path = Path(self.app.state.settings.upload_dir) / f"{document['id']}.pdf"
        self.assertTrue(saved_path.exists())

        deleted = self.client.delete(
            f"/api/v1/documents/{document['id']}",
            headers=self.authorization(self.user_token),
        )
        self.assertEqual(deleted.status_code, 204, deleted.text)
        self.assertFalse(saved_path.exists())
        not_found = self.client.get(
            f"/api/v1/documents/{document['id']}",
            headers=self.authorization(self.user_token),
        )
        self.assertEqual(not_found.status_code, 404)


if __name__ == "__main__":
    unittest.main()
