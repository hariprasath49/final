from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class MaterialRequest(models.Model):
    _name = 'material.request'
    
    def _get_default_location_id(self):
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
    def _get_default_location_dest_id(self):
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
    @api.model
    def _get_default_picking_type(self):
        return self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            ('warehouse_id.company_id', 'in', [self.env.context.get('company_id', self.env.user.company_id.id), False])],
            limit=1).id
    
    name = fields.Char(readonly=True,required=True, copy=False, default='New')
    requester_name = fields.Many2one('res.partner',string="Name",required=True)
    date_of_request = fields.Date(string="Date Of Request")
    product_ids = fields.One2many('material.request.line', 'product_id', string="Product")
    picking_type_id = fields.Many2one('stock.picking.type', string="Picking Type",default=_get_default_picking_type, required=True)
    move_type = fields.Selection([('direct', 'Partial'), ('one', 'All at Onces')], String='Delivery Type', default='direct',required=True)
    location_id = fields.Many2one('stock.location',default=_get_default_location_id,string="Production Location",required=True)
    location_dest_id = fields.Many2one('stock.location', 'Destination Location',default=_get_default_location_dest_id,required=True)
    state = fields.Selection([('draft', 'Draft'),('issued', 'Issued')],default='draft')
    product_id = fields.Many2one('product.product',string="Product")
    bom_id = fields.Many2one('mrp.bom',string="Bill of Material")
    pass_order_ids = fields.Many2one('mrp.production',string="test")
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('material.request') or 'New'
        result = super(MaterialRequest, self).create(vals)
        return result
    
    @api.multi
    def issue_product(self):
        print "tests"
        list=[]
        for rec in self.product_ids:
            list.append((0,0, { 'name':rec.id,
                                'product_id':rec.product_id.id,
                                'date': rec.create_date,
                                'product_uom_qty': rec.product_uom_qty,
                                'product_uom': rec.product_uom.id,
                                'location_id':rec.location_id.id,
                                'location_dest_id':rec.location_dest_id.id,
                                }))
        
        material_request = self.env['stock.picking'].create({
                        'partner_id':self.requester_name.id,
                        'min_date':self.date_of_request,
                        'move_type':self.move_type,
                        'picking_type_id':self.picking_type_id.id,
                        'location_id':self.location_id.id,
                        'location_dest_id':self.location_dest_id.id,
                        'move_lines':list
                        })
                
        
    

class MaterialRequestLine(models.Model):
    _name = 'material.request.line'
    def _get_default_location_id(self):
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
    def _get_default_location_dest_id(self):
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
    
    product_id = fields.Many2one('product.product',string="Product")
    product_uom_qty = fields.Float(string="Quantity Required",required=True)
    price_unit = fields.Float(string="Unit Price")
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    location_id = fields.Many2one('stock.location', 'Production Location',default=_get_default_location_id,required=True)
    create_date = fields.Date(string='Current Date', default=datetime.today())
    location_dest_id = fields.Many2one('stock.location', 'Destination Location',default=_get_default_location_dest_id,required=True)
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    state = fields.Selection(selection_add=[('transfer', 'Transfered')])
    material_id = fields.Many2one('material.request')
    
    @api.one
    def state_transfer(self):
        self.state = 'transfer'
        if self.state == 'transfer':
            self.env['material.request'].write({'state': 'issued'})
        
        
class mrp_production(models.Model):
    _inherit = 'mrp.production'
    picking_type_id = fields.Many2one('stock.picking.type',string="Picking Type")
    
    
    @api.multi
    def action_related_mo(self):
        count_id = self.env['material.request'].search([('pass_order_ids', '=', self.id)])
        print count_id
        action = self.env.ref('material_request.material_request_list')
        print action    
        return {
            'name': action.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(action.id, 'tree')],
            'target': 'current',
            'res_model': 'material.request',
            'domain': [('pass_order_ids', '=', self.id)],
        }
        
    @api.multi
    def action_create_mo(self):
        list=[]
        for rec in self.move_raw_ids:
            list.append((0,0, { 'name':rec.id,
                                'product_id':rec.product_id.id,
                                'product_uom_qty': rec.product_uom_qty,
                                'product_uom': rec.product_uom.id,
                                }))
        material_request = self.env['material.request'].create({'requester_name':self.user_id.id,
                                                                'date_of_request':self.date_planned_start,
                                                                'product_id':self.product_id.id,
                                                                'bom_id':self.bom_id.id,
                                                                'picking_type_id':self.picking_type_id.id,
                                                                'product_ids':list,
                                                                'pass_order_ids': self.id,
                                                                })
        
        
        
        
        
        
        
        
