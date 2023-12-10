{
    "name": "Product stock by location widget",
    "summary": "Product stock by location widget",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "author": "Borovlev A.S.",
    "company": "Simbioz Holding",
    "depends": [
        "stock",
    ],
    "data": [
        "views/assets.xml",
        "views/product_views.xml",
        "views/stock_location_views.xml",
    ],
    "qweb": [
        "static/src/xml/stock_by_location_widget.xml",
    ],
    "excludes": ["product_stock_by_location"],
    "installable": True,
}
