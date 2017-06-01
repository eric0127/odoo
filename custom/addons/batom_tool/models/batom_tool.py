# -*- coding: utf-8 -*-
# Copyright <2016> <Batom Co., Ltd.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import logging
import math
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from datetime import datetime

_logger = logging.getLogger(__name__)

class BatomCutterGroup(models.Model):
    _name = 'batom.cutter.group'
    _description = 'Cutter Group'
    
    name = fields.Char('Cutter Group Name')

class BatomCutterClass(models.Model):
    _name = 'batom.cutter.class'
    _description = 'Cutter Class'
    
    name = fields.Char('Cutter Class Name')
    
class BatomCutterModel(models.Model):
    _name = "batom.cutter.model"
    _description = 'Cutter Model'
    _order = 'cutter_group_id, cutter_model_code'
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the cutter model without removing it.")
    cutter_model_code = fields.Char('Cutter Model Code', ) # 刀具型號
    cutter_group_id = fields.Many2one('batom.cutter.group', string='Cutter Group')
    image_file = fields.Binary('Image File', attachment=True) # 圖面
    image_file_name = fields.Char('Image File Name')
    cutter_ids =  fields.One2many('batom.cutter', 'cutter_model_id', 'Cutters')
    cutter_count = fields.Integer('# Cutters', compute='_compute_cutter_count')
    model_history_ids = fields.One2many('batom.cutter.model.history', 'cutter_model_id', 'Model History List') # 履歷表
    product_ids = fields.Many2many(
        comodel_name='product.product', relation='batom_cutter_model_product_rel',
        column1='cutter_model_id', column2='product_id', string='Used by Products')
    product_ids_code = fields.Char(string='Used by Products', compute='_compute_product_code', store=True)
    supplier_id = fields.Many2one('res.partner', string='Supplied by')
    cutter_class_id = fields.Many2one('batom.cutter.class', string='Cutter Class') # 刀具種類
    material = fields.Char('Material') # Material
    type = fields.Char('TYPE') # TYPE
    mod = fields.Float('MOD') # MOD
    dp = fields.Float('DP') # DP
    pa = fields.Float('PA') # PA
    teeth = fields.Char('Teeth (Workpiece)') # Teeth(工件)
    od = fields.Float('OD') # OD
    length = fields.Float('Length') # Length
    bore = fields.Float('Bore') # Bore
    df = fields.Float('D+F (Workpiece)') # D+F(工件)
    coating = fields.Char('Coating') # coating
    dressing_cost = fields.Monetary('Dressing Cost', currency_field='dressing_cost_currency_id') # 修刀費用
    dressing_cost_currency_id = fields.Many2one('res.currency', string='Dressing Cost Currency',
        default=lambda self: self.env.user.company_id.currency_id)
    sharpening_cost = fields.Monetary('Sharpening Cost', currency_field='sharpening_cost_currency_id') # 磨刀費
    sharpening_cost_currency_id = fields.Many2one('res.currency', string='Sharpening Cost Currency',
        default=lambda self: self.env.user.company_id.currency_id)
    titanium_cost = fields.Monetary('Titanium Cost', currency_field='titanium_cost_currency_id') # 鍍鈦費
    titanium_cost_currency_id = fields.Many2one('res.currency', string='Titanium Cost Currency',
        default=lambda self: self.env.user.company_id.currency_id)
    allowed_sharpening = fields.Char('Allowed Sharpening') # 可磨刃長
    standard_sharpening = fields.Char('Standard Sharpening') # 標準研磨量
    allowed_sharpening_times = fields.Integer('Allowed Sharpening Times') # 可磨次數
    model_notes = fields.Text('Model Notes') # 注意事項
    model_remarks = fields.Text('Model Remarks')
    protuberance = fields.Float('Protuberance', digits=(12,3)) # 瘤頭
    root_diameter = fields.Char('Root Diameter') # 齒底俓
    semitopping_amount = fields.Char('Semitopping Amount') # 齒頂倒角
    stock_removal = fields.Float('Stock Removal') # 刮磨留量
    number_threads = fields.Char('Number of Threads') # 牙口數
    gash_lead = fields.Char('Gash Lead') # 刃溝槽導程
    class_accuracy = fields.Char('Class of Accuracy') # 精度
    cutter_teeth = fields.Char('Teeth (Cutter)') # Teeth (刀具)

    _sql_constraints = [
        ('code_uniq', 'unique (cutter_model_code)', 'The model code must be unique.')
    ]

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {},
                       cutter_model_code = _("%s (Copy)") % self.cutter_model_code,
                       model_history_ids = None)
        return super(BatomCutterModel, self).copy(default=default)

    @api.one
    @api.depends('cutter_model_code')
    def _compute_name(self):
        if self.cutter_model_code:
            self.name = self.cutter_model_code

    @api.one
    @api.depends('product_ids')
    def _compute_product_code(self):
        product_code = None
        if self.product_ids:
            for product in self.product_ids:
                if product_code:
                    product_code += ", "
                else:
                    product_code = ""
                product_code += product.default_code
        self.product_ids_code = product_code

    @api.one
    @api.depends('cutter_ids', 'cutter_ids.total')
    def _compute_cutter_count(self):
        if self.cutter_ids:
            self.cutter_count = sum(self.mapped('cutter_ids').mapped('total'))
        else:
            self.cutter_count = 0
    
    @api.multi
    def action_view_cutter(self):
        action = self.env.ref('batom_tool.product_open_cutter').read()[0]
        action['domain'] = [('id', 'in', self.cutter_ids.ids)]
        return action
    
class BatomCutter(models.Model):
    _name = "batom.cutter"
    _description = 'Cutter Information'
    _inherits = {'batom.cutter.model': 'cutter_model_id'}
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the cutter without removing it.")
    state = fields.Selection([ # 狀態
        ('material', u'物料'),
        ('bought', u'進貨'),
        ('consigned', u'進貨-客供'),
        ('sold', u'進貨-轉賣'),
        ],
        string='State',
        index=True,
        )
    managing_department = fields.Selection([ # 管理單位
        ('procurement', u'採購'),
        ('production', u'生產'),
        ],
        string='Managing Department',
        default='procurement',
        index=True,
        )
    cutter_model_id = fields.Many2one('batom.cutter.model', string='Cutter Model', required=True, ondelete="cascade")
    batom_code = fields.Char('Batom Code') # 本土編號
    supplier_code = fields.Char('Vendor Cutter Code') # 廠商刀具編號
    history_ids = fields.One2many('batom.cutter.history', 'cutter_id', 'History List') # 履歷表
    history_file = fields.Binary('History File', attachment=True) # 圖面
    history_file_name = fields.Char('History File Name')
    inquiry_number = fields.Char('Inquiry/Order Number') # 詢/訂價編號
    product_code = fields.Char('Used by Products in Excel') # 工件編號
    supplier = fields.Char('Supplier Name in Excel') # 刀具製造商
    price = fields.Monetary('Price', currency_field='price_currency_id') # 單價
    price_currency_id = fields.Many2one('res.currency', string='Price Currency',
        default=lambda self: self.env.user.company_id.currency_id)
    exchange_rate = fields.Float('Exchange Rate') # 匯率
    tax = fields.Monetary('Tax', currency_field='tax_currency_id') # 稅
    tax_currency_id = fields.Many2one('res.currency', string='Tax Currency',
        default=lambda self: self.env.user.company_id.currency_id)
    shipping = fields.Monetary('Shipping Cost', currency_field='shipping_currency_id') # 運費
    shipping_currency_id = fields.Many2one('res.currency', string='Shipping Cost Currency',
        default=lambda self: self.env.user.company_id.currency_id)
    year = fields.Date('Year') # 年份
    total = fields.Integer('Quantity') # Total
    consigned_to = fields.Char('Consigned To in Excel') # 保管廠商
    consigned_to_id = fields.Many2one('res.partner', string='Consigned To', domain="[('is_company','=',True), ('supplier','=',True)]")
    consigned_date = fields.Char('Consigned Date') # 保管日期
    returned_date = fields.Char('Returned Date') # 歸還日期
    storage = fields.Char('Batom Storage') # 本土保管處
    remarks = fields.Text('Remarks') # 備註
    inquiry_form = fields.Binary('Inquiry Form') # 詢價單
    inquiry_form_name = fields.Char('Inquiry Form File Name')
    supplier_quotation = fields.Binary('Supplier Quotation') # 供應商報價單
    supplier_quotation_name = fields.Char('Supplier Quotation File Name')
    purchase_request = fields.Binary('Purchase Request') # 採購申請單
    purchase_request_name = fields.Char('Purchase Request File Name')
    purchase_order = fields.Binary('Purchase Order') # 訂購單
    purchase_order_name = fields.Char('Purchase Order File Name')
    order_confirmation = fields.Binary('Order Confirmation') # 訂單確認
    order_confirmation_name = fields.Char('Order Confirmation File Name')
    invoice = fields.Binary('Invoice') # Invoice
    invoice_name = fields.Char('Invoice File Name')
    order_date = fields.Date('Order Date') # 訂購日期
    expected_delivery_date = fields.Date('Expected Delivery Date') # 期望交期
    status = fields.Selection([ # 現況
        ('available', u'可用'),
        ('in-use', u'使用中'),
        ('maintenance', u'修刀中'),
        ('purchasing', u'採購中'),
        ('scrapped', u'報廢'),
        ('unknown', u'不明'),
        ],
        string='Status',
        default='unknown',
        index=True,
        )
    notes = fields.Text('Notes') # 注意事項

    _sql_constraints = [
        ('code_uniq', 'unique (batom_code)', 'The Batom cutter code must be unique.')
    ]

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {},
            active = self.active,
            state = self.state,
            managing_department = self.managing_department,
            cutter_model_id = self.cutter_model_id.id,
            batom_code = _("%s (Copy)") % self.batom_code,
            total = 1,
            year = datetime.today(),
            status = 'unknown',
            history_ids = None,
            history_file = None,
            history_file_name = None,
            inquiry_number = None,
            product_code = None,
            supplier = None,
            price = None,
            price_currency_id = None,
            exchange_rate = None,
            tax = None,
            tax_currency_id = None,
            shipping = None,
            shipping_currency_id = None,
            consigned_to = None,
            consigned_to_id = None,
            consigned_date = None,
            returned_date = None,
            storage = None,
            remarks = None,
            inquiry_form = None,
            inquiry_form_name = None,
            supplier_quotation = None,
            supplier_quotation_name = None,
            purchase_request = None,
            purchase_request_name = None,
            purchase_order = None,
            purchase_order_name = None,
            order_confirmation = None,
            order_confirmation_name = None,
            invoice = None,
            invoice_name = None,
            order_date = None,
            expected_delivery_date = None,
            notes = None,
            )
        return super(BatomCutter, self).copy(default=default)

    @api.one
    @api.depends('batom_code')
    def _compute_name(self):
        if self.batom_code:
            self.name = self.batom_code

class BatomCutterHistoryAction(models.Model):
    _name = 'batom.cutter.action'
    _description = 'Cutter History Action'
    
    name = fields.Char('Cutter History Action')
    is_out = fields.Boolean('Out Action', default=False)
    is_in = fields.Boolean('In Action', default=False)

class BatomCutterHisory(models.Model):
    _name = "batom.cutter.history"
    _description = 'Cutter History'
    _order = 'date desc'
    
    active = fields.Boolean(
        'Active', compute='_compute_active', store=True)
    cutter_id = fields.Many2one('batom.cutter', 'Cutter', required=True, index=True)
    date = fields.Date('Date', required=False, default=lambda self: fields.datetime.now())
    action_id = fields.Many2one('batom.cutter.action', string='Action')
    sharpening_mm = fields.Float('Sharpening Amount (mm)')
    processed_quantity = fields.Integer('# Parts Processed')
    cost = fields.Monetary('Cost', currency_field='cost_currency_id')
    cost_currency_id = fields.Many2one('res.currency', string='Cost Currency',
        default=lambda self: self.env.user.company_id.currency_id)
    vendor_id = fields.Many2one('res.partner', string='Vendor',  domain="[('is_company','=',True), ('supplier','=',True)]")
    remarks = fields.Text('Remarks') # 備註
    attached_file = fields.Binary('Attached File', attachment=True)
    attached_file_name = fields.Char('Attached File Name')
    managing_department = fields.Selection([ # 管理單位
        ('procurement', u'採購'),
        ('production', u'生產'),
        ],
        string='Managing Department',
        default='procurement',
        compute='_compute_managing_department',
        )

    @api.one
    @api.depends('cutter_id')
    def _compute_managing_department(self):
        if self.cutter_id:
            self.managing_department = self.cutter_id.managing_department

    @api.one
    @api.depends('cutter_id', 'cutter_id.active')
    def _compute_active(self):
        if self.cutter_id.active:
            self.active = True
        else:
            self.active = False

class BatomCutterModelHisory(models.Model):
    _name = "batom.cutter.model.history"
    _description = 'Cutter Model History'
    _order = 'date desc'
    
    active = fields.Boolean(
        'Active', compute='_compute_active', store=True)
    cutter_model_id = fields.Many2one('batom.cutter.model', 'Cutter Model', required=True, index=True)
    date = fields.Date('Date', required=False, default=lambda self: fields.datetime.now())
    remarks = fields.Text('Remarks') # 備註
    attached_file = fields.Binary('Attached File', attachment=True)
    attached_file_name = fields.Char('Attached File Name')

    @api.one
    @api.depends('cutter_model_id', 'cutter_model_id.active')
    def _compute_active(self):
        if self.cutter_model_id.active:
            self.active = True
        else:
            self.active = False

class ProductTemplate(models.Model):
    _inherit = "product.template"

    cutter_model_count = fields.Integer('# Cutter Models', compute='_compute_cutter_model_count')
    cutter_count = fields.Integer('# Cutters', compute='_compute_cutter_count')

    def _compute_cutter_model_count(self):
        self.cutter_model_count = sum(self.mapped('product_variant_ids').mapped('cutter_model_count'))

    def _compute_cutter_count(self):
        self.cutter_count = sum(self.mapped('product_variant_ids').mapped('cutter_count'))
    
    @api.multi
    def action_template_view_cutter(self):
        action = self.env.ref('batom_tool.template_open_cutter').read()[0]
        action['domain'] = [('id', 'in', self.product_variant_ids.cutter_ids.ids)]
        return action
    
class ProductProduct(models.Model):
    _inherit = "product.product"

    cutter_model_ids = fields.Many2many(
        comodel_name='batom.cutter.model', relation='batom_cutter_model_product_rel',
        column1='product_id', column2='cutter_model_id', string='Using Cutter Models')
    cutter_model_count = fields.Integer('# Cutter Models', compute='_compute_cutter_model_count')
    cutter_ids = fields.One2many('batom.cutter', compute='_compute_cutter_ids', string='Using Cutters')
    cutter_count = fields.Integer('# Cutters', compute='_compute_cutter_count')

    def _compute_cutter_model_count(self):
        if self.cutter_model_ids:
            self.cutter_model_count = len(self.cutter_model_ids)
        else:
            self.cutter_model_count = 0
            
    def _compute_cutter_ids(self):
        if self.cutter_model_ids:
            cutter_ids = []
            for cutter_model_id in self.cutter_model_ids:
                cutter_ids.extend(cutter_model_id.cutter_ids.ids)
            self.cutter_ids = cutter_ids

    def _compute_cutter_count(self):
        if self.cutter_ids:
            self.cutter_count = len(self.cutter_ids)
        else:
            self.cutter_count = 0
    
    @api.multi
    def action_view_cutter(self):
        action = self.env.ref('batom_tool.product_open_cutter').read()[0]
        action['domain'] = [('id', 'in', self.cutter_ids.ids)]
        return action
    
class ResPartner(models.Model):
    _inherit = "res.partner"

    supplier_cutter_model_ids = fields.One2many(
        'batom.cutter.model', 'supplier_id', string='Supplying Cutter Models')
    supplier_cutter_model_count = fields.Integer('# Cutter Models', compute='_compute_supplier_cutter_model_count')
    supplier_cutter_ids = fields.One2many('batom.cutter', compute='_compute_supplier_cutter_ids', string='Supplying Cutters')
    supplier_cutter_count = fields.Integer('# Cutters', compute='_compute_supplier_cutter_count')

    customer_product_ids = fields.Many2many(
        comodel_name='product.product', relation='batom_customer_product_rel',
        column1='partner_id', column2='product_id', string='Products for Customer')
    customer_cutter_model_count = fields.Integer('# Cutter Models', compute='_compute_customer_cutter_model_count')
    customer_cutter_ids = fields.One2many('batom.cutter', compute='_compute_customer_cutter_ids', string='Using Cutters')
    customer_cutter_count = fields.Integer('# Cutters', compute='_compute_customer_cutter_count')

    @api.one
    def _compute_supplier_cutter_model_count(self):
        if self.supplier_cutter_model_ids:
            self.supplier_cutter_model_count = len(self.supplier_cutter_model_ids)
        else:
            self.supplier_cutter_model_count = 0
            
    @api.one
    def _compute_supplier_cutter_ids(self):
        if self.supplier_cutter_model_ids:
            cutter_ids = []
            for cutter_model_id in self.supplier_cutter_model_ids:
                cutter_ids.extend(cutter_model_id.cutter_ids.ids)
            self.supplier_cutter_ids = cutter_ids

    @api.one
    def _compute_supplier_cutter_count(self):
        if self.supplier_cutter_ids:
            self.supplier_cutter_count = len(self.supplier_cutter_ids)
        else:
            self.supplier_cutter_count = 0
            
    @api.one
    def _compute_customer_cutter_ids(self):
        if self.customer_product_ids:
            cutter_ids = []
            for product in self.customer_product_ids:
                for cutter_model_id in product.cutter_model_ids:
                    cutter_ids.extend(cutter_model_id.cutter_ids.ids)
            self.customer_cutter_ids = cutter_ids

    @api.one
    def _compute_customer_cutter_count(self):
        if self.customer_cutter_ids:
            self.customer_cutter_count = len(self.customer_cutter_ids)
        else:
            self.customer_cutter_count = 0
    
    @api.multi
    def action_supplier_view_cutter(self):
        action = self.env.ref('batom_tool.partner_open_cutter').read()[0]
        action['domain'] = [('id', 'in', self.supplier_cutter_ids.ids)]
        return action
    
    @api.multi
    def action_customer_view_cutter(self):
        action = self.env.ref('batom_tool.partner_open_cutter').read()[0]
        action['domain'] = [('id', 'in', self.customer_cutter_ids.ids)]
        return action
