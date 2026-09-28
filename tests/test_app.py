import io
import unittest

import pandas as pd

from app import (
    compute_row_tags,
    deduplicate_contacts,
    normalize_phone_for_identity,
    prepare_contacts,
    process_single_file,
)


class ConverterTests(unittest.TestCase):
    def test_blank_emails_fall_back_to_phone(self):
        contacts = pd.DataFrame(
            {
                "email": ["", "", ""],
                "phone_number": ["2094056699", "4155550100", "6505550100"],
            }
        )

        result = deduplicate_contacts(contacts)

        self.assertEqual(len(result), 3)

    def test_phone_formatting_does_not_create_duplicates(self):
        contacts = pd.DataFrame(
            {
                "email": ["", ""],
                "phone_number": ["+1 (209) 405-6699", "209-405-6699"],
            }
        )

        result = deduplicate_contacts(contacts)

        self.assertEqual(len(result), 1)

    def test_primary_email_remains_the_preferred_identity(self):
        contacts = pd.DataFrame(
            {
                "email": ["Person@Example.com", " person@example.com "],
                "phone_number": ["2094056699", "4155550100"],
            }
        )

        result = deduplicate_contacts(contacts)

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["phone_number"], "2094056699")

    def test_rows_without_email_or_phone_are_not_collapsed(self):
        contacts = pd.DataFrame(
            {
                "email": ["", None, "nan"],
                "phone_number": ["", None, "none"],
            }
        )
        contacts.index = [0, 0, 0]

        result = deduplicate_contacts(contacts)

        self.assertEqual(len(result), 3)

    def test_short_phone_placeholders_are_not_used_as_identity(self):
        contacts = pd.DataFrame(
            {
                "email": ["", ""],
                "phone_number": ["0", "0"],
            }
        )

        result = deduplicate_contacts(contacts)

        self.assertEqual(len(result), 2)

    def test_phone_normalization_preserves_non_us_numbers(self):
        self.assertEqual(
            normalize_phone_for_identity("+44 20 7946 0958"),
            "442079460958",
        )

    def test_prepare_contacts_does_not_add_internal_columns(self):
        contacts = pd.DataFrame(
            {
                "email": [" PERSON@EXAMPLE.COM "],
                "secondary_email": [None],
                "phone_number": [" (209) 405-6699 "],
                "first_name": [" John "],
            }
        )

        result = prepare_contacts(contacts)

        self.assertEqual(list(result.columns), list(contacts.columns))
        self.assertEqual(result.iloc[0]["email"], "person@example.com")
        self.assertEqual(result.iloc[0]["secondary_email"], "")
        self.assertEqual(result.iloc[0]["phone_number"], "(209) 405-6699")
        self.assertEqual(result.iloc[0]["first_name"], "John")

    def test_single_file_conversion_schema_is_unchanged(self):
        csv_file = io.StringIO(
            "first_name,last_name,phone_1,email_1,email_2,address,city,state,"
            "zip_code,insight\n"
            "John,Pacelli,2094056699,,,PO Box 10890,Zephyr Cove,NV,89448,"
            "Visited listing\n"
        )

        result, missing_columns = process_single_file(csv_file, tags="weekly")

        self.assertIsNone(missing_columns)
        self.assertEqual(
            list(result.columns),
            [
                "first_name",
                "last_name",
                "phone_number",
                "email",
                "secondary_email",
                "street_address",
                "city",
                "state_abbrev",
                "postal_code",
                "note",
                "source",
                "tags",
            ],
        )
        self.assertEqual(result.iloc[0]["phone_number"], "2094056699")
        self.assertEqual(result.iloc[0]["source"], "realintent")
        self.assertEqual(result.iloc[0]["tags"], "89448, weekly")

    def test_compute_row_tags_tiers_and_zip(self):
        row_tier_1 = pd.Series(
            {
                "zip_code": "34653",
                "Pre-Movers": "x",
                "Residential": "X",
                "Mortgages": "x",
            }
        )
        self.assertEqual(
            compute_row_tags(row_tier_1), "34653, RealScout Tier 1"
        )

        row_tier_2 = pd.Series(
            {
                "zip_code": "34653.0",
                "Residential": "x",
                "Brokers And Agents": "x",
            }
        )
        self.assertEqual(
            compute_row_tags(row_tier_2), "34653, RealScout Tier 2"
        )

        row_tier_3 = pd.Series(
            {
                "zip_code": "926",
                "Mortgages": "x",
            }
        )
        self.assertEqual(
            compute_row_tags(row_tier_3), "00926, RealScout Tier 3"
        )

        row_no_tier = pd.Series({"zip_code": "34653"})
        self.assertEqual(compute_row_tags(row_no_tier), "34653")

        row_with_manual = pd.Series({"zip_code": "34653", "Residential": "x"})
        self.assertEqual(
            compute_row_tags(row_with_manual, manual_tags="VIP"),
            "34653, RealScout Tier 3, VIP",
        )

    def test_single_file_conversion_with_intent_tiers(self):
        csv_file = io.StringIO(
            "first_name,last_name,phone_1,email_1,email_2,address,city,state,"
            "zip_code,insight,Pre-Movers,Residential,Mortgages\n"
            "Jane,Doe,4155550100,,,123 Main St,Tampa,FL,33601,"
            "Listing inquiry,x,x,x\n"
        )

        result, missing_columns = process_single_file(csv_file)
        self.assertIsNone(missing_columns)
        self.assertEqual(result.iloc[0]["tags"], "33601, RealScout Tier 1")


if __name__ == "__main__":
    unittest.main()
