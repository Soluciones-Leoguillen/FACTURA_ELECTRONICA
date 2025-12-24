# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import requests
import base64
import traceback


class AccountMove(models.Model):
    _inherit = 'account.move'

    clave_documento = fields.Char(
        string="",
        required=False,
        tracking=True,
        copy=False,
    )
    consecutivo = fields.Char(
        string="Consecutivo",
        copy=False,
        tracking=True,
        readonly=True,
    )

    tipoVenta = fields.Selection(
        string="Tipo de Venta",
        selection=[
            ('1', 'Contado'),
            ('2', 'Crédito'),
        ],
        required=False,
        tracking=True,
        default="1",
        copy=False,
    )

    envio_gti = fields.Selection(
        string="Tipo de Envío",
        selection=[
            ('Enviar a GTI', 'Enviar a GTI'),
            ('No Enviar a GTI', 'No Enviar a GTI'),
        ],
        required=True,
        tracking=True,
        default= 'Enviar a GTI',
        copy=False,
    )


    plazoVenta = fields.Selection(
        string="Días de Credito",
        selection=[
            ('0', '0 Días'),
            ('30', '30 Días'),
            ('30', '30 Días'),
            ('60', '60 Días'),
            ('90', '90 Días'),
        ],
        required=False,
        tracking=True,
        default="0",
        copy=False,
    )

    economic_activity_id = fields.Many2one(
        comodel_name="economic.activity", string="Actividad económica",
        context={"active_test": False},
        default=lambda self: self.env.company.economic_activity_id or False,
        copy=False
    )
    economic_activities_ids = fields.Many2many(
        comodel_name="economic.activity",
        string="Actividades económicas",
        compute="_compute_economic_activities",
        context={"active_test": False},
        copy=False
    )

    receiver_economic_activity_id = fields.Many2one(
        comodel_name="economic.activity",
        string="Actividad económica del receptor",)
    receiver_economic_activities_ids = fields.Many2many(
        comodel_name="economic.activity",
        related="partner_id.economic_activities_ids",
        string="Actividades económicas del receptor",
    )
    documento_hacienda_id = fields.Many2one(
        comodel_name="documento.hacienda",
        string="Documento Hacienda",
        copy=False,
    )

    xml_document = fields.Binary(string="Documento XML", copy=False, attachment=True)
    fname_xml_document = fields.Char(string="Documento XML file name", copy=False)

    xml_response = fields.Binary(string="XML Respuesta", copy=False, attachment=True)
    fname_xml_response = fields.Char(string="XML Respuesta file name", copy=False)

    xml_supplier_approval = fields.Binary(string="XML Aprobación Proveedor", copy=False, attachment=True)
    fname_xml_supplier_approval = fields.Char(string="XML Aprobación Proveedor file name", copy=False)

    pdf_document = fields.Binary(string="Documento PDF", copy=False, attachment=True)
    fname_pdf_document = fields.Char(string="Documento PDF file name", copy=False)
    gti_document_state = fields.Selection(
        selection=[
            ('100', 'El documento se encuentra con estado aceptado en Hacienda'),
            ('101', 'El documento se encuentra con estado procesando o recibido en Hacienda'),
            ('102', 'El documento se encuentra con estado rechazado en Hacienda'),
            ('103', 'El documento se encuentra con estado de error en Hacienda'),
            ('104', 'No se encontró el documento en la base de datos de GTI'),
            ('105', 'El documento se encuentra pendiente de enviar a Hacienda'),
            ('106', 'El documento aún no tiene respuesta de Hacienda'),
            ('107', 'El documento tiene un estado desconocido en Hacienda'),
            ('108', 'Por favor, vuelva a realizar la consulta del documento más tarde'),
        ],
        string="Estado FE",
        copy=False,
    )
    gti_document_state_description = fields.Text(
        string="Descripción Estado FE",
        copy=False,
    )
    payment_method = fields.Selection(
        string="Método de pago",
        selection=[
            ('1', 'Efectivo'),
            ('2', 'Tarjeta'),
            ('3', 'Cheque'),
            ('4', 'Transferencia o depósito bancario'),
            ('5', 'Recaudo por terceros'),
            ('6', 'SINPE Móvil'),
            ('7', 'Plataforma Digital'),
            ('99', 'Otros'),
        ],
        tracking=True,
    )
    tipo_documento = fields.Selection(
        selection=[
            ("1", "Factura Electrónica"),
            # ("2", "Nota de Débito Electrónica"),
            ("3", "Nota de Crédito Electrónica"),
            ("4", "Tiquete Electrónico"),
            # ("5", "Confirmación de Aceptación del Comprobante Electrónico"),
            # ("6", "Confirmación de Aceptación Parcial del Comprobante Electrónico"),
            # ("7", "Confirmación de Rechazo del Comprobante Electrónico"),
            # ("8", "Factura Electrónica de Compra"),
            # ("9", "Factura Electrónica de Exportación"),
            # ("10", "Recibo Electrónico de Pago"),
        ],
        string="Tipo de Documento",
        default=lambda self: '1' if (self._context.get('move_type') == 'out_invoice' or self._context.get('default_move_type') == 'out_invoice') else False
    )

    @api.onchange('tipo_documento')
    def _onchange_tipo_documento(self):
        for rec in self:
            move_type = rec.move_type or rec._context.get('move_type') or rec._context.get('default_move_type') or False
            if rec.tipo_documento == '3' and move_type == 'out_invoice':
                raise ValidationError("El tipo de documento no coincide con el documento que se está creando.")

    @api.onchange('move_type')
    def _onchange_move_type(self):
        for rec in self:
            if rec.move_type == 'out_invoice':
                rec.tipo_documento = '1'

    @api.depends("partner_id", "company_id")
    def _compute_economic_activities(self):
        for inv in self:
            company_id = self.env.company
            if inv.move_type in ("in_invoice", "in_refund") and inv.partner_id:
                inv.economic_activities_ids = company_id.economic_activities_ids
            elif inv.move_type in ("out_invoice", "out_refund"):
                inv.economic_activities_ids = company_id.economic_activities_ids
            else:
                inv.economic_activities_ids = False

    def enviar_factura(self):
        for data in self:
            # validaciones
            if not data.partner_id.vat:
                raise ValidationError("El cliente no tiene número de identificación")
            if not data.partner_id.tipo_Identificacion:
                raise ValidationError("El cliente no tiene tipo de identificación")
            if not data.company_id.economic_activity_id:
                raise ValidationError("La compañía no tiene código de actividad")
            if not data.company_id.gti_NumCuenta:
                raise ValidationError("La compañía no tiene número de cuenta")
            if not data.company_id.gti_Usuario:
                raise ValidationError("La compañía no tiene usuario")
            if not data.company_id.gti_Clave:
                raise ValidationError("La compañía no tiene clave")
            if not data.company_id.gti_url:
                raise ValidationError("El ambiente de la compañía está en 'Deshabilitado'")
            if not data.tipo_documento:
                raise ValidationError("El tipo de documento no está establecido")
            # cabys
            for line in data.invoice_line_ids:
                if not line.product_id.cabys:
                    raise ValidationError(f"El producto {line.product_id.name} no tiene código CABYS")
                if not line.tax_ids:
                    raise ValidationError(f"La línea {line.name} no tiene impuestos")
                for tax in line.tax_ids:
                    if not tax.codigo_Imp:
                        raise ValidationError(f"El impuesto {tax.name} no tiene código de tarifa")
            if data.move_type in ('out_invoice', 'out_refund') and data.envio_gti == 'Enviar a GTI':
                if not data.reversed_entry_id:  # TODO cambiar a uso de tipo_documento en los if
                    vals = {
                        "name": data.name,
                        "tipo": data.tipo_documento,
                        "codigo": "1",
                        "factura": data.id,
                        "company_id": data.company_id.id,
                    }
                else:
                    vals = {
                        "name": data.name,
                        "tipo": data.tipo_documento,
                        "codigo": "1",
                        "factura_NC": data.id,
                        "factura": data.reversed_entry_id.id,
                        "company_id": data.company_id.id,
                    }

                if not data.documento_hacienda_id:
                    res = self.env['documento.hacienda'].sudo().create(vals)
                    data.documento_hacienda_id = res.id

                    if not data.reversed_entry_id:
                        res.crear_factura()
                    else:
                        res.crear_nota_credito()
                else:
                    if not data.reversed_entry_id:
                        data.documento_hacienda_id.crear_factura()
                    else:
                        data.documento_hacienda_id.crear_nota_credito()

    def check_document(self):
        url = f"{self.company_id.gti_url}/Documentos/EstadoHacienda"
        params = {
            'pNumCuenta': self.company_id.gti_NumCuenta,
            'pConsecutivo': self.consecutivo,
            'pUsuario': self.company_id.gti_Usuario,
            'pClave': self.company_id.gti_Clave,
        }
        response = requests.post(url, params=params, timeout=30)
        if response.status_code == 200:
            request = response.json()
            if 'Codigo' in request:
                self.write({
                    'gti_document_state': request.get('Codigo', ''),
                    'gti_document_state_description': request.get('Detalle', ''),
                })
        else:
            raise ValidationError(_(f'Error al descargar XML: {response.status_code}. Espere unos minutos y vuelva a intentar.'))

    def get_xml(self):
        url = f"{self.company_id.gti_url}/Documentos/ConsultaXMLEnviado"
        params = {
            'pNumCuenta': self.company_id.gti_NumCuenta,
            'pConsecutivo': self.consecutivo,
            'pUsuario': self.company_id.gti_Usuario,
            'pClave': self.company_id.gti_Clave,
        }
        response = requests.post(url, params=params, timeout=30)
        if response.status_code == 200:
            xml_content = response.content
            if self.tipo_documento == '1':
                type = 'FE'
            elif self.tipo_documento == '3':
                type = 'NC'
            elif self.tipo_documento == '4':
                type = 'TE'
            else:
                type = 'DOC'
            self.write({
                'xml_document': base64.b64encode(xml_content),
                'fname_xml_document': f"{type}_{self.consecutivo}.xml"
            })
        else:
            raise ValidationError(_(f'Error al descargar XML: {response.status_code}'))

    def get_response_xml(self):
        url = f"{self.company_id.gti_url}/Documentos/ConsultaXMLRespuesta"
        params = {
            'pNumCuenta': self.company_id.gti_NumCuenta,
            'pConsecutivo': self.consecutivo,
            'pUsuario': self.company_id.gti_Usuario,
            'pClave': self.company_id.gti_Clave,
        }
        response = requests.post(url, params=params, timeout=30)
        if response.status_code == 200:
            xml_content = response.content
            self.write({
                'xml_response': base64.b64encode(xml_content),
                'fname_xml_response': f"Respuesta_{self.consecutivo}.xml"
            })
        else:
            raise UserError(_(f'Error al descargar XML: {response.status_code}: {response.text} Espere unos minutos y vuelva a intentar.'))

    def action_check_document(self):
        try:
            self.check_document()
            self.get_xml()
            self.get_response_xml()
        except Exception as e:
            tb = traceback.format_exc()
            raise UserError(_(f'Error: {str(e)}\n{tb}'))
