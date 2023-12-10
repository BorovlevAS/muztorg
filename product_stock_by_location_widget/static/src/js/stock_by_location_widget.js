odoo.define("product_stock_by_location_widget.stock_by_location_widget", function (require) {
    const AbstractField = require("web.AbstractField");
    const core = require("web.core");
    const QWeb = core.qweb;
    const fieldRegistry = require("web.field_registry");

    const _t = core._t;

    const StockByLocationWidget = AbstractField.extend({
        description: _t("Stock remainigs"),
        className: "o_field_remainigs",
        supportedFieldTypes: ["char"],
        buttonTemplate: "stock_by_location",
        popoverTemplate: "stock_by_location_popover",
        popoverTitleTemplate: "stock_by_location_popover_title",
        popoverContentTemplate: "stock_by_location_popover_content",

        init: function () {
            this._super.apply(this, arguments);
        },

        _render: function () {
            const self = this;
            const value = JSON.parse(this.value);
            if (!value) {
                this.$el.html("");
                return;
            }
            this.parsed_value = value;
            this.$el.html(QWeb.render(this.buttonTemplate));
            this.$el.find("a").prop("special_click", true);
            this.$('[data-toggle="popover"]').each(function () {
                $(this).popover({
                    container: self.nodeOptions.container ? this : "body",
                    html: true,
                    placement: "auto",
                    title: $(QWeb.render(self.popoverTitleTemplate, {})),
                    content: $(QWeb.render(self.popoverContentTemplate, self.parsed_value)),
                    trigger: "focus",
                    delay: {show: 0, hide: 100},
                    // ,template: QWeb.render(self.popoverTemplate, {}),
                });
            });
        },

        destroy: function () {
            this.$el.find("a").popover("dispose");
            this._super.apply(this, arguments);
        },
    });

    fieldRegistry.add("stock_by_location_widget", StockByLocationWidget);

    return StockByLocationWidget;
});
