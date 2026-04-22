{
    'name': 'Integración GTI',
    'version': '2.0',
    'category': 'Facturación Electrónica',
    'summary': 'Facturación Electrónica Costa Rica — GTI API v4.4',
    'sequence': -100,
    'description': """
Integración GTI v2.0 — Facturación Electrónica Costa Rica
==========================================================
Mejoras v2.0:
- Redondeo GTI HALF_UP (corrige errores en USD con decimales)
- Totales calculados desde líneas redondeadas (evita error 61/62)
- TotalImpVenta + TotalImpOtros separados
- Descarga PDF de Hacienda + adjunta al chatter
- NC parciales (por líneas, no solo total)
- Banners de estado FE en factura
- Estado FE en lista de facturas con filtros
- Errores detallados en chatter
- Botón re-enviar en caso de error
- EsVersion4_4 en JSON
- CABYS servicios corregido (7,8,9)

Autor: Leo Guillen - odoo@leoguillen.com
    """,
    'author': 'Leo Guillen',
    'website': 'http://leoguillen.com',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'account',
        'sale',
        'hr',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/discount_code_data.xml',
        'data/economic_activity_data.xml',
        'data/uom_data.xml',
        'data/res_currency_data.xml',
        # Wizards
        # 'wizard/sa_estudiante_pre_matricula_wizard_view.xml',
        # Views
        'views/view_cajero_menu.xml',
        'views/uom_views.xml',
        'views/res_currency_views.xml',
        'views/view_product_template_inherit.xml',
        'views/view_product_product_inherit.xml',
        'views/view_res_company_inherit.xml',
        'views/view_account_move_inherit.xml',
        'views/view_config_settings.xml',
        'views/view_res_partner_inherit.xml',
        'views/view_account_tax_inherit.xml',
        'views/view_cajero.xml',
        'views/view_documento_hacienda.xml',

        # reports
        # 'report/report_accion_personal_vacaciones.xml'

    ],
    'assets': {
        'web.assets_backend': [
            # 'sa_periodo/static/src/js/sa_periodo_dashboard.js',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
