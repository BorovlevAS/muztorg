# -*- coding: utf-8 -*-
{
    "name": "BIKO: Модуль добавляет поля в сделку, которые используются в сервисе",
    "version": "14.0.1.1.0",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": [
        "crm",
        "biko_base_module",
    ],
    "data": [
        "views/crm_lead_vews.xml",
        "views/pick_points_views.xml",
        "security/ir_access_roles.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
