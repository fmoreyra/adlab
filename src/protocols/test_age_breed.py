"""Tests for protocol age and breed form normalization."""

from datetime import date

from django.test import TestCase

from accounts.models import User, Veterinarian
from accounts.test_helpers import ensure_veterinarian_profile_complete
from protocols.age_utils import compose_age_string, parse_age_string
from protocols.choices import BREED_OTHER, BREEDS_BY_SPECIES
from protocols.forms import CytologyProtocolForm, ProtocolEditForm
from protocols.models import Protocol


class AgeUtilsTest(TestCase):
    """Unit tests for age string helpers."""

    def test_compose_empty(self):
        self.assertEqual(compose_age_string(None, None), "")
        self.assertEqual(compose_age_string(0, 0), "")

    def test_compose_years_only(self):
        self.assertEqual(compose_age_string(5, None), "5 años")
        self.assertEqual(compose_age_string(1, None), "1 año")

    def test_compose_months_only(self):
        self.assertEqual(compose_age_string(None, 6), "6 meses")
        self.assertEqual(compose_age_string(None, 1), "1 mes")

    def test_compose_years_and_months(self):
        self.assertEqual(compose_age_string(2, 3), "2 años 3 meses")

    def test_parse_round_trip(self):
        years, months = parse_age_string("2 años 3 meses")
        self.assertEqual(years, 2)
        self.assertEqual(months, 3)
        self.assertEqual(
            compose_age_string(years, months),
            "2 años 3 meses",
        )

    def test_parse_years_only(self):
        self.assertEqual(parse_age_string("5 años"), (5, None))

    def test_parse_months_only(self):
        self.assertEqual(parse_age_string("6 meses"), (None, 6))

    def test_parse_legacy_unparseable(self):
        self.assertEqual(parse_age_string("adulto"), (None, None))


class ProtocolAgeBreedFormTest(TestCase):
    """Integration tests for age and breed mixins."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="vet-age@example.com",
            username="vet-age",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
            is_staff=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            first_name="Ana",
            last_name="García",
            license_number="MP-99999-AGE",
            phone="+54 341 1234567",
            email="vet-age@example.com",
        )
        ensure_veterinarian_profile_complete(self.veterinarian)

    def _base_cytology_data(self):
        return {
            "species": "Canino",
            "animal_identification": "Max",
            "presumptive_diagnosis": "Sospecha de linfoma",
            "submission_date": date.today(),
            "technique_used": "Punción (PAAF)",
            "sampling_site": "Linfonódulo",
            "number_of_slides": 1,
        }

    def test_cytology_form_composes_age(self):
        data = {
            **self._base_cytology_data(),
            "age_years": 2,
            "age_months": 3,
            "breed": "Labrador Retriever",
        }
        form = CytologyProtocolForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        protocol = form.save(veterinarian=self.veterinarian)
        self.assertEqual(protocol.age, "2 años 3 meses")
        self.assertEqual(protocol.breed, "Labrador Retriever")

    def test_cytology_form_empty_age(self):
        data = self._base_cytology_data()
        form = CytologyProtocolForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        protocol = form.save(veterinarian=self.veterinarian)
        self.assertEqual(protocol.age, "")

    def test_cytology_form_breed_other(self):
        data = {
            **self._base_cytology_data(),
            "breed": BREED_OTHER,
            "breed_other": "Cruza personalizada",
        }
        form = CytologyProtocolForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        protocol = form.save(veterinarian=self.veterinarian)
        self.assertEqual(protocol.breed, "Cruza personalizada")

    def test_cytology_form_breed_other_required(self):
        data = {
            **self._base_cytology_data(),
            "breed": BREED_OTHER,
            "breed_other": "",
        }
        form = CytologyProtocolForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("breed_other", form.errors)

    def test_edit_form_prefills_legacy_age_and_breed(self):
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            breed="Raza Legacy XYZ",
            age="5 años",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
            status=Protocol.Status.DRAFT,
        )
        form = ProtocolEditForm(instance=protocol)
        self.assertEqual(form.fields["age_years"].initial, 5)
        self.assertIsNone(form.fields["age_months"].initial)
        self.assertEqual(form.fields["breed"].initial, BREED_OTHER)
        self.assertEqual(form.fields["breed_other"].initial, "Raza Legacy XYZ")

    def test_breeds_catalog_has_all_species(self):
        for species in [
            "Canino",
            "Felino",
            "Bovino",
            "Equino",
            "Ovino",
            "Caprino",
            "Porcino",
            "Aviar",
            "Otro",
        ]:
            self.assertIn(species, BREEDS_BY_SPECIES)
            self.assertIn(BREED_OTHER, BREEDS_BY_SPECIES[species])
