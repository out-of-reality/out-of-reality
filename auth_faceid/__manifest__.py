{
    "name": "Auth FaceID",
    "version": "17.0.1.0.0",
    "author": "Out of reality",
    "license": "LGPL-3",
    "website": "https://github.com/out-of-reality/out-of-reality",
    "depends": ["web"],
    "external_dependencies": {"python": ["dlib", "face_recognition", "python-jose"]},
    "data": [
        "views/login_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    "assets": {
        "web.assets_frontend": [
            "auth_faceid/static/src/login_faceid/**/*",
        ],
    },
}
