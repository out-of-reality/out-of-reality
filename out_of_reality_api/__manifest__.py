{
    "name": "Out of Reality API",
    "version": "17.0.1.0.0",
    "category": "API",
    "author": "Out of reality",
    "license": "LGPL-3",
    "website": "https://github.com/out-of-reality/out-of-reality",
    "depends": ["fastapi", "auth_faceid"],
    "data": [
        "data/api_data.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    "post_init_hook": "post_init_hook",
}
