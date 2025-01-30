{
    "name": "Clinic Management",
    "version": "17.0.1.0.0",
    "author": "Out of reality",
    "license": "LGPL-3",
    "website": "https://github.com/out-of-reality/out-of-reality",
    "depends": ["web", "portal", "contacts", "web_widget_mpld3_chart"],
    "external_dependencies": {
        "python": ["opencv-python", "matplotlib", "mediapipe", "numpy"]
    },
    "data": [
        "data/mail_template_data.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/clinic_game_session_views.xml",
        "views/res_partner_views.xml",
        "views/health_insurance_views.xml",
        "views/res_users_views.xml",
        "views/clinic_management_menu.xml",
        "views/clinic_portal_templates.xml",
    ],
    "demo": [
        "demo/health_insurance.xml",
        "demo/res_partner.xml",
        "demo/res_users.xml",
        "demo/res_users_link.xml",
        "demo/clinic_game_session.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "assets": {"web.assets_backend": ["clinic_management/static/src/components/**/*"]},
}
