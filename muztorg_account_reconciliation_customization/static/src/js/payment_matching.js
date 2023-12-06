odoo.define("muztorg_account_reconciliation_customization.ReconciliationClientAction", function (require) {
    const {StatementAction} = require("base_accounting_kit.ReconciliationClientAction");

    StatementAction.include({
        _onSearch: function (ev) {
            var self = this;
            this.model.domain = ev.domain;
            this.model.display_context = "search";
            self.reload().then(function () {
                self.renderer._updateProgressBar({
                    valuenow: self.model.valuenow,
                    valuemax: self.model.valuemax,
                });
            });
        },
    });
});
