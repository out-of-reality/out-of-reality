{
    'name': 'Clinic Management',
    'version': "17.0.1.0.0",
    'author': 'Franco Leyes - Augusto Caceres - Santiago Agüero',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/clinic_game_session_views.xml',
        'views/clinic_management_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'clinic_management/static/src/components/**/*',
        ],
    }
}
