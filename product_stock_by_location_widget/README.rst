===============================
Product stock by location widget
===============================

#. Widget which shows the stock of the product by location.

Installation
============

To install this module, you need to:

#. Just install the module.

Configuration
=============

To configure this module, you need to:

#. Nothing to configure

Usage
=====

#. Just Use the module.
#. If you need to add widget in the other views you need to take field json_remainings_popover from product model (product.product or product.template) and add fields to the view, using next code::

    <field
      name="json_remainings_popover"
      string=" "
      widget="stock_by_location_widget"
      attrs="{'invisible':[('type', 'not in', ['product', 'consu'])]}"
    />

