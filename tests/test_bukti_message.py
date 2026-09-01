import unittest

from Services.bukti_maker_service import format_uploaded_files_message


class TestUploadedFilesMessage(unittest.TestCase):
    def test_formats_multiple_names(self):
        result = format_uploaded_files_message([
            "Bukti TF 1.pdf",
            "Bukti TF 2.pdf",
        ])

        self.assertEqual(
            result,
            "1. Bukti TF 1.pdf\n2. Bukti TF 2.pdf\n\nMohon untuk segera di follow up dan diproses lebih lanjut. Terima kasih.",
        )


if __name__ == "__main__":
    unittest.main()
