{
    "name": "BIKO: site integration (base)",
    "version": "14.0.1.0.0",
    "author": "Zhmyhova T.N.",
    "company": "BIKO Solutions",
    "depends": [
        "base",
        "phone_validation",
    ],
    "data": [
        "security/ir_access_roles.xml",
        "security/ir.model.access.csv",
        "views/site_integration_menus_views.xml",
        "views/site_integration_settings_views.xml",
        # "views/site_integration_fields_views.xml",
        "views/site_integration_setting_views.xml",
        "wizards/site_integration_sinc.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["transliterate", "python-xml2dict"]},
    "application": True,
    "auto_install": False,
}
