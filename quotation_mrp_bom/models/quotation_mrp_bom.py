# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class quotation_mrp_bom(models.Model):
    _name = "quotation.mrp_bom"
    _rec_name="name"
    quotation_mrp_bom_line = fields.One2many("quotation.mrp_bom.line",'quotation_mrp_bom_id')
    code = fields.Char('Reference',help="The Internal Reference for the BOM so as to Differentiate it from other BOM for similar Product")
    active = fields.Boolean(
        'Active', default=True,
        help="If the active field is set to False, it will allow you to hide the bills of material without removing it.")
    type = fields.Selection([
        ('normal', 'Manufacture this product'),
        ('phantom', 'Kit')], 'BoM Type',
        default='normal', required=True,help="Type og BOM")
    name=fields.Char('Name of the Quotation BOM' , index=True, default=lambda self: _('New'))
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product',
        domain="[('type', 'in', ['product', 'consu'])]")
    product_id = fields.Many2one(
        'product.product', 'Product Variant',
        domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]",
        help="If a product variant is defined the BOM is available only for this product.")
    product_qty = fields.Float('Quantity', default=1.0,help="Quantity of the Product")
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',oldname='product_uom',help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of bills of material.")
    company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env['res.company']._company_default_get('mrp.bom'),required=True)
    order_id=fields.Many2one('sale.order','Sale Order',help="The Quotation from which the Quotation BOM was made")    
    order_line_id=fields.Many2one('sale.order.line','Sale Order Line',help="The Quotation Line from which the Quotation BOM was made")    
    mrp_bom_number = fields.Integer(compute='_compute_mrp_bom_nos', string="Number of MRP BOM",help="The number of BOM made against this Quotation BOM")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True,store="True")
    # OneToMAny field for mapping the bom made against the quotation bom
    mrp_bom_ids=fields.One2many('mrp.bom','quotation_mrp_bom_id')
    description=fields.Text(string="Description",required=True,help="Description of the Product")
    total=fields.Monetary(string="Amount Total",readonly=True,compute='_amount_all')
    @api.depends('quotation_mrp_bom_line.price_subtotal')
    def _amount_all(self):
        for order in self:
            amt_total=0
            for line in order.quotation_mrp_bom_line:
                amt_total+=line.price_subtotal
            order.update({
                'total':amt_total
            })
    # @api.depends('quotation_mrp_bom_line.unit_price')
    # def _amount_all(self):
    #     for order in self:
    #         amt_total=0
    #         for line in order.quotation_mrp_bom_line:
    #             amt_total+=line.unit_price
    #         order.update({
    #             'total':amt_total
    #         })
    @api.depends('quotation_mrp_bom_line')
    def _compute_mrp_bom_nos(self):
        for quotation_bom in self:
            nbr = 0
            for order in quotation_bom.mrp_bom_ids:
                if order.id:
                    nbr += 1
            quotation_bom.mrp_bom_number = nbr
    @api.model
    def create(self,vals):
        if vals:
            vals['name'] = self.env['ir.sequence'].next_by_code("quotation.mrp.bom")
        new_id = super(quotation_mrp_bom,self).create(vals)
        return new_id
    
class quotation_mrp_bom_line(models.Model):
    _name = "quotation.mrp_bom.line"
    quotation_mrp_bom_id = fields.Many2one("quotation.mrp_bom")
    name=fields.Char("Description",required=True,help="Description of the Product")
    product_id = fields.Many2one('product.product',string="Product")    
    product_qty = fields.Float('Product Quantity',help="Quantity of the product")
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',oldname='product_uom',help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")
    sequence = fields.Integer('Sequence', default=1,help="Gives the sequence order when displaying.")
    attribute_value_ids = fields.Many2many('product.attribute.value', string='Variants',help="BOM Product Variants needed form apply this line.")
    active=fields.Boolean('Active',default=True)
    unit_price=fields.Float(string="Cost Price")
    price_subtotal=fields.Float(string='Sub Total',readonly=True,compute='set_price_subtotal',store=True)
    @api.onchange('product_id','unit_price')
    def _set_unit_price(self):
        if self.unit_price:
            self.unit_price=self.unit_price
        else:
            self.unit_price=self.product_id.standard_price
    @api.depends('unit_price','product_qty')
    def set_price_subtotal(self):
        for order in self:
            order.price_subtotal=order.product_qty * order.unit_price