import os
import tempfile
from unittest.mock import patch

from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from ..routers import videos


class TestVideoRoutes(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_fastapi_running_user = cls.env.ref("base.user_admin")
        cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create(
            {
                "name": "Test Patient",
                "partner_type": "patient",
                "self_managed": True,
            }
        )

    @patch("odoo.addons.out_of_reality_api.routers.videos.convert_video_to_h264_ffmpeg")
    def test_upload_video_success(self, mock_convert):
        def mock_convert_side_effect(input_path, output_path):
            with open(output_path, "wb") as f:
                f.write(b"fake converted video content")
            return True

        mock_convert.side_effect = mock_convert_side_effect

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_file.write(b"fake mp4 video content for testing")
            tmp_file_path = tmp_file.name

        try:
            with open(tmp_file_path, "rb") as f:
                files = {"video": ("test.mp4", f, "video/mp4")}

                with self._create_test_client(router=videos.router) as test_client:
                    response = test_client.post("/upload/", files=files)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "uploaded")
            self.assertIn("filename", response.json())
            mock_convert.assert_called_once()

        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_upload_video_invalid_format(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"fake content")
            tmp_file_path = tmp_file.name

        try:
            with open(tmp_file_path, "rb") as f:
                files = {"video": ("test.txt", f, "text/plain")}

                with self._create_test_client(router=videos.router) as test_client:
                    response = test_client.post("/upload/", files=files)

            self.assertEqual(response.status_code, 400)
            self.assertIn("Only .mp4 files are allowed", response.json()["detail"])

        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    @patch("odoo.addons.out_of_reality_api.routers.videos.convert_video_to_h264_ffmpeg")
    @patch("odoo.addons.out_of_reality_api.routers.videos._logger")
    def test_upload_video_conversion_failure(self, mock_logger, mock_convert):
        mock_convert.return_value = False

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_file.write(b"fake mp4 video content for testing")
            tmp_file_path = tmp_file.name

        try:
            with open(tmp_file_path, "rb") as f:
                files = {"video": ("test.mp4", f, "video/mp4")}

                with self._create_test_client(router=videos.router) as test_client:
                    response = test_client.post("/upload/", files=files)

            self.assertEqual(response.status_code, 500)
            self.assertIn("Video conversion failed", response.json()["detail"])
            # Verify that the error would have been logged (but we mocked it)
            mock_logger.error.assert_called_once()

        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
