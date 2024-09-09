{
    'name': 'Out of Reality API',
    'version': "17.0.1.0.0",
    'category': 'API',
    'author': 'Franco Leyes - Augusto cáceres - Santiago Agüero',
    'license': 'LGPL-3',
    'depends': ['fastapi'],
    'data': [
        'data/api_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'post_init_hook'
}
