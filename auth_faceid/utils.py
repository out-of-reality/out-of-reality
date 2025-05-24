import requests

FACE_SERVICE_URL = "http://face_recognition:5000"


class FaceIDService:
    @classmethod
    def identify_user(cls, image_b64, env):
        if not image_b64:
            return {"success": False, "message": "No image data received."}

        try:
            encoding_res = requests.post(
                f"{FACE_SERVICE_URL}/face_encoding",
                json={"image_b64": image_b64},
                timeout=5,
            )
            if encoding_res.status_code != 200:
                return {"success": False, "message": "No face detected."}

            captured_encoding = encoding_res.json().get("encoding")

            users = env["res.users"].sudo().search([("face_encoding", "!=", False)])
            if not users:
                return {"success": False, "message": "No users with face encodings."}

            user_encodings = [u.face_encoding.decode() for u in users]

            compare_res = requests.post(
                f"{FACE_SERVICE_URL}/compare_faces",
                json={
                    "captured_encoding": captured_encoding,
                    "user_encodings": user_encodings,
                },
                timeout=5,
            )
            if compare_res.status_code != 200:
                return {"success": False, "message": "Face comparison failed."}

            matched_index = compare_res.json().get("matched_index")
            if matched_index is not None:
                return {"success": True, "user": users[matched_index]}

            return {"success": False, "message": "No match found."}

        except Exception as e:
            return {"success": False, "message": str(e)}
