"""
Tests for laboratory staff delegated protocol creation (roadmap 7.1).
"""

from datetime import date

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from accounts.test_helpers import create_complete_veterinarian_user
from protocols.lab_protocol import LAB_PROTOCOL_VET_SESSION_KEY
from protocols.models import Protocol, ProtocolStatusHistory


class LabProtocolCreateFlowTest(TestCase):
    """End-to-end tests for lab-delegated protocol creation."""

    def setUp(self):
        """Create lab staff and verified/unverified veterinarians."""
        self.lab_user = User.objects.create_user(
            email="lab@example.com",
            username="lab",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
        )
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="testpass123",
            role=User.Role.ADMIN,
            email_verified=True,
        )
        self.verified_vet_user, self.verified_vet = (
            create_complete_veterinarian_user(
                email="verified@example.com",
                username="verified",
                email_verified=True,
                vet_kwargs={
                    "first_name": "Ana",
                    "last_name": "García",
                    "license_number": "MP-99999",
                },
            )
        )
        self.unverified_vet_user, self.unverified_vet = (
            create_complete_veterinarian_user(
                email="unverified@example.com",
                username="unverified",
                email_verified=False,
                vet_kwargs={
                    "first_name": "Bob",
                    "last_name": "López",
                    "license_number": "MP-88888",
                },
            )
        )
        self.client = Client()

    def _login_lab(self):
        self.client.login(email="lab@example.com", password="testpass123")

    def _login_admin(self):
        self.client.login(email="admin@example.com", password="testpass123")

    def _login_vet(self):
        self.client.login(email="verified@example.com", password="testpass123")

    def _select_veterinarian(self, veterinarian):
        session = self.client.session
        session[LAB_PROTOCOL_VET_SESSION_KEY] = veterinarian.pk
        session.save()

    def test_search_returns_only_verified_veterinarians(self):
        """Search only lists veterinarians with verified email."""
        self._login_lab()
        response = self.client.get(
            reverse("protocols:lab_protocol_search"),
            {"query": "García"},
        )

        self.assertEqual(response.status_code, 200)
        veterinarians = response.context["veterinarians"]
        self.assertEqual(len(veterinarians), 1)
        self.assertEqual(veterinarians[0].pk, self.verified_vet.pk)

    def test_default_list_shows_enabled_veterinarians(self):
        """GET without query shows paginated list of enabled veterinarians."""
        self._login_lab()
        response = self.client.get(reverse("protocols:lab_protocol_search"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_search"])
        self.assertGreaterEqual(response.context["total_count"], 1)
        vet_pks = {vet.pk for vet in response.context["veterinarians"]}
        self.assertIn(self.verified_vet.pk, vet_pks)
        self.assertNotIn(self.unverified_vet.pk, vet_pks)

    def test_unverified_veterinarian_not_in_search(self):
        """Unverified veterinarian does not appear in search results."""
        self._login_lab()
        response = self.client.get(
            reverse("protocols:lab_protocol_search"),
            {"query": "López"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["veterinarians"]), 0)

    def test_veterinarian_cannot_access_lab_create_urls(self):
        """Veterinarians are denied access to lab create routes."""
        self._login_vet()
        urls = [
            reverse("protocols:lab_protocol_search"),
            reverse("protocols:lab_protocol_select_type"),
            reverse("protocols:lab_protocol_create_cytology"),
            reverse("protocols:lab_protocol_create_histopathology"),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, msg=url)

    def test_lab_creates_cytology_protocol_with_audit_fields(self):
        """Lab staff creates cytology protocol for selected veterinarian."""
        self._login_lab()
        self._select_veterinarian(self.verified_vet)

        form_data = {
            "species": "Canino",
            "animal_identification": "Rex",
            "presumptive_diagnosis": "Masa cutánea",
            "submission_date": date.today(),
            "technique_used": "Punción (PAAF)",
            "sampling_site": "Piel",
            "number_of_slides": 2,
        }
        response = self.client.post(
            reverse("protocols:lab_protocol_create_cytology"),
            data=form_data,
        )

        self.assertEqual(response.status_code, 302)
        protocol = Protocol.objects.get(animal_identification="Rex")
        self.assertEqual(protocol.veterinarian, self.verified_vet)
        self.assertEqual(protocol.created_by, self.lab_user)
        self.assertEqual(protocol.status, Protocol.Status.DRAFT)
        self.assertEqual(
            protocol.analysis_type, Protocol.AnalysisType.CYTOLOGY
        )

        history = ProtocolStatusHistory.objects.filter(protocol=protocol)
        self.assertTrue(
            history.filter(
                description="Cargado por personal de laboratorio"
            ).exists()
        )

    def test_lab_creates_histopathology_protocol(self):
        """Lab staff creates histopathology protocol for selected veterinarian."""
        self._login_lab()
        self._select_veterinarian(self.verified_vet)

        form_data = {
            "species": "Felino",
            "animal_identification": "Michi",
            "presumptive_diagnosis": "Biopsia",
            "submission_date": date.today(),
            "material_submitted": "Tejido cutáneo",
            "number_of_containers": 1,
            "preservation": "Formol",
        }
        response = self.client.post(
            reverse("protocols:lab_protocol_create_histopathology"),
            data=form_data,
        )

        self.assertEqual(response.status_code, 302)
        protocol = Protocol.objects.get(animal_identification="Michi")
        self.assertEqual(protocol.veterinarian, self.verified_vet)
        self.assertEqual(protocol.created_by, self.lab_user)
        self.assertEqual(
            protocol.analysis_type, Protocol.AnalysisType.HISTOPATHOLOGY
        )

    def test_lab_submits_draft_generates_temporary_code(self):
        """Lab staff can submit a draft and generate temporary code."""
        self._login_lab()
        protocol = Protocol.objects.create(
            veterinarian=self.verified_vet,
            created_by=self.lab_user,
            species="Canino",
            animal_identification="DraftLab",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.DRAFT,
        )

        response = self.client.post(
            reverse("protocols:protocol_submit", kwargs={"pk": protocol.pk})
        )

        self.assertEqual(response.status_code, 302)
        protocol.refresh_from_db()
        self.assertEqual(protocol.status, Protocol.Status.SUBMITTED)
        self.assertTrue(protocol.temporary_code)

        history = ProtocolStatusHistory.objects.filter(
            protocol=protocol,
            status=Protocol.Status.SUBMITTED,
        ).first()
        self.assertEqual(
            history.description,
            "Protocolo enviado por personal de laboratorio",
        )

    def test_admin_can_access_lab_create_flow(self):
        """Admin users may load protocols via lab create URLs."""
        self._login_admin()
        response = self.client.get(reverse("protocols:lab_protocol_search"))
        self.assertEqual(response.status_code, 200)

    def test_select_type_redirects_without_session_vet(self):
        """Create flow requires veterinarian selection in session."""
        self._login_lab()
        response = self.client.get(
            reverse("protocols:lab_protocol_select_type")
        )
        self.assertRedirects(
            response, reverse("protocols:lab_protocol_search")
        )

    def test_cannot_select_unverified_veterinarian(self):
        """POST with unverified vet id is rejected."""
        self._login_lab()
        response = self.client.post(
            reverse("protocols:lab_protocol_search"),
            {"veterinarian_id": self.unverified_vet.pk},
        )
        self.assertRedirects(
            response, reverse("protocols:lab_protocol_search")
        )
        self.assertNotIn(LAB_PROTOCOL_VET_SESSION_KEY, self.client.session)

    def test_lab_search_page_accessible_from_dashboard_url(self):
        """Lab search view renders for authenticated lab staff."""
        self._login_lab()
        response = self.client.get(reverse("protocols:lab_protocol_search"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "protocols/lab_protocol_veterinarian_search.html"
        )
