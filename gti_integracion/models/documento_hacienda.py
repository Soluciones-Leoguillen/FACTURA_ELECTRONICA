# -*- coding: utf-8 -*-
# documento_hacienda.py v2.0 — Mejoras GTI v4.4
#
# v2.0: gti_round HALF_UP, totales desde líneas, PDF chatter,
#       NC parciales, TotalImpVenta/TotalImpOtros, EsVersion4_4,
#       CABYS servicios 7-9, errores detallados chatter

import base64
import json
import math
import logging
import re
from datetime import datetime

import pytz
import requests

from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def gti_round(value, decimals=2):
    """Redondeo GTI HALF_UP: 5 siempre sube.
    Ref: Instructivo API Carga Factura v4.4."""
    if value is None:
        return 0.0
    multiplier = 10 ** decimals
    return math.floor(float(value) * multiplier + 0.5) / multiplier


CABYS_SERVICE_PREFIXES = ('7', '8', '9')
IVA_TAX_CODES = (1, 7, 8)
CURRENCY_MAP = {'CRC': 1, 'USD': 2, 'EUR': 3}


def _strip_html(html_text):
    """Texto plano desde HTML sin depender de website."""
    if not html_text:
        return ''
    return re.sub(r'<[^>]+>', '', str(html_text)).strip()


class DocumentoHacienda(models.Model):
    _name = "documento.hacienda"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Información de los Documentos de Hacienda"
    _order = 'create_date desc'

    name = fields.Char(string="Nombre", required=True, tracking=True)
    activo = fields.Boolean(string="Activo", default=True, tracking=True)
    clave = fields.Char(string="Clave", tracking=True)
    fecha_Emsion = fields.Datetime(string="Fecha Emisión", tracking=True)
    consecutivo = fields.Char(string="Consecutivo", tracking=True)
    consecutivo_Interno = fields.Char(string="Consecutivo GTI", tracking=True)
    tipo = fields.Selection(
        selection=[
            ('1', 'Factura electrónica'),
            ('2', 'Nota de débito electrónica'),
            ('3', 'Nota de crédito electrónica'),
            ('4', 'Tiquete electrónico'),
            ('8', 'Factura electrónica de compra'),
            ('9', 'Factura electrónica de exportación'),
        ],
        string="Tipo", required=True, tracking=True,
    )
    codigo = fields.Char(string="Código Respuesta", tracking=True)
    codigo_descripcion = fields.Text(string="Descripción Error", tracking=True)
    factura = fields.Many2one('account.move', string='Factura')
    factura_NC = fields.Many2one('account.move', string='Factura NC')
    factura_ND = fields.Many2one('account.move', string='Factura ND')
    company_id = fields.Many2one(
        'res.company', string='Empresa', required=True,
        default=lambda self: self.env.company,
    )
    json_data = fields.Text(string="JSON Enviado", tracking=True)
    gti_raw_response = fields.Text(string="Respuesta GTI (Raw)")

    @property
    def _deci(self):
        return 2

    # ═══════════════════════════════════════════════════════════════
    # FACTURA ELECTRÓNICA
    # ═══════════════════════════════════════════════════════════════
    def crear_factura(self):
        """Construir y enviar FE/TE a GTI."""
        self.ensure_one()
        if self.consecutivo and self.codigo == '0':
            raise UserError(_('Este documento ya fue emitido exitosamente.'))

        move = self.factura
        factura = self._build_encabezado(move)

        if move.partner_id and move.partner_id.vat:
            factura['Documentos'][0]['Encabezado']['Receptor'] = (
                self._build_receptor(move))

        lines_data = self._build_lineas(move)
        factura['Documentos'][0]['Lineas'] = [ld['json'] for ld in lines_data]
        factura['Documentos'][0]['Totales'] = self._build_totales(lines_data)
        factura['Documentos'][0]['Otros'] = {
            'Notas': _strip_html(move.narration) or 'Sin Notas'}
        factura['Documentos'][0]['Extra'] = {'EsVersion4_4': True}

        self._enviar_documento(factura, move)

    # ═══════════════════════════════════════════════════════════════
    # NOTA DE CRÉDITO — v2.0: NC parciales
    # ═══════════════════════════════════════════════════════════════
    def crear_nota_credito(self):
        """NC parcial o total. Usa líneas de la NC, no de la original."""
        self.ensure_one()
        if self.consecutivo and self.codigo == '0':
            raise UserError(_('Este documento ya fue emitido exitosamente.'))

        move_nc = self.factura_NC
        if not move_nc:
            raise UserError(_('No se encontró la factura de Nota de Crédito.'))

        factura = self._build_encabezado(move_nc)

        if move_nc.partner_id and move_nc.partner_id.vat:
            factura['Documentos'][0]['Encabezado']['Receptor'] = (
                self._build_receptor(move_nc))

        lines_data = self._build_lineas(move_nc)
        factura['Documentos'][0]['Lineas'] = [ld['json'] for ld in lines_data]
        factura['Documentos'][0]['Totales'] = self._build_totales(lines_data)
        factura['Documentos'][0]['Referencia'] = self._build_referencia()
        factura['Documentos'][0]['Otros'] = {
            'Notas': _strip_html(move_nc.narration) or 'Nota de Crédito'}
        factura['Documentos'][0]['Extra'] = {'EsVersion4_4': True}

        self._enviar_documento(factura, move_nc)

    # ═══════════════════════════════════════════════════════════════
    # ENVIAR A GTI
    # ═══════════════════════════════════════════════════════════════
    def _enviar_documento(self, factura_json, move):
        """Enviar JSON a GTI y procesar respuesta con detalle en chatter."""
        self.json_data = json.dumps(factura_json, indent=2, ensure_ascii=False)
        company = move.company_id

        if not company.gti_url:
            raise UserError(_(
                'El ambiente GTI no está configurado. '
                'Vaya a Ajustes → Empresa → Ambiente.'))

        url = '%s/Documentos/CargarDocumento' % company.gti_url
        params = {
            'pUsuario': company.gti_Usuario,
            'pClave': company.gti_Clave,
            'pNumCuenta': company.gti_NumCuenta,
        }

        try:
            response = requests.post(
                url, headers={'Content-Type': 'application/json', 'Accept': 'text/plain'},
                json=factura_json, params=params, timeout=60, verify=False)
        except requests.exceptions.Timeout:
            raise UserError(_('Tiempo de espera agotado con GTI. Reintente.'))
        except requests.exceptions.ConnectionError:
            raise UserError(_('No se pudo conectar con GTI. Verifique internet.'))
        except Exception as e:
            raise UserError(_('Error comunicación GTI: %s') % str(e))

        self.gti_raw_response = response.text[:5000]

        if response.status_code not in (200, 202):
            self._post_gti_error(move, 'HTTP',
                'Error HTTP %s: %s' % (response.status_code, response.text[:500]))
            return

        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError):
            self._post_gti_error(move, '99',
                'Respuesta no es JSON válido: %s' % response.text[:500])
            return

        respuestas = data.get('Respuestas', [{}])
        if not respuestas:
            self._post_gti_error(move, '99', 'Respuesta vacía de GTI')
            return

        req = respuestas[0]
        codigo = str(req.get('Codigo', '99'))
        self.codigo = codigo

        if codigo == '0':
            consecutivo = str(req.get('Consecutivo', ''))
            clave = str(req.get('ClaveNumerica', ''))
            self.consecutivo = consecutivo
            self.clave = clave
            self.consecutivo_Interno = str(req.get('IdDocumento', ''))
            self.codigo_descripcion = 'Emisión exitosa'

            move.write({'consecutivo': consecutivo, 'clave_documento': clave})

            move.message_post(body=Markup(
                '<div style="background:#e8f5e9;border:1px solid #4caf50;'
                'border-radius:4px;padding:8px;margin:4px 0;">'
                '<strong style="color:#2e7d32;">✓ Factura Electrónica '
                'emitida exitosamente</strong>'
                '<br/><b>Consecutivo:</b> %s'
                '<br/><b>Clave:</b> <span style="font-family:monospace;'
                'font-size:0.85em;">%s</span></div>'
            ) % (consecutivo, clave))
        else:
            desc = req.get('DescripcionError', req.get('Detalle', 'Error desconocido'))
            self._post_gti_error(move, codigo, desc)

    def _post_gti_error(self, move, codigo, descripcion):
        """Publicar error detallado en chatter."""
        self.codigo = str(codigo)
        self.codigo_descripcion = descripcion
        move.message_post(body=Markup(
            '<div style="background:#ffebee;border:1px solid #f44336;'
            'border-radius:4px;padding:8px;margin:4px 0;">'
            '<strong style="color:#c62828;">⚠ Error Factura Electrónica</strong>'
            '<br/><b>Código:</b> %s'
            '<br/><b>Error:</b> %s'
            '<br/><small style="color:#666;">Corrija los datos y presione '
            '<b>«Enviar a GTI»</b> para reintentar.</small></div>'
        ) % (codigo, descripcion))
        _logger.warning('GTI ERROR %s para %s: %s', codigo, move.name, descripcion)

    # ═══════════════════════════════════════════════════════════════
    # ENCABEZADO
    # ═══════════════════════════════════════════════════════════════
    def _build_encabezado(self, move):
        company = move.company_id
        cajero = self.env['cajero'].sudo().search(
            [('empleadoAsignado', '=', self.env.user.id)], limit=1)
        if not cajero:
            raise UserError(_('El usuario no está asignado a ninguna caja.'))

        activity = move.economic_activity_id or company.economic_activity_id
        if not activity or not activity.code:
            raise UserError(_('No hay actividad económica configurada.'))

        currency_name = move.currency_id.name if move.currency_id else 'CRC'
        self.fecha_Emsion = datetime.now()

        header = {
            'TipoDoc': int(self.tipo),
            'SituacionEnvio': 1,
            'CantDeci': self._deci,
            'Sucursal': int(cajero.sucursal or 1),
            'CodigoActividad': activity.code,
            'Terminal': int(cajero.terminal or 1),
            'Moneda': CURRENCY_MAP.get(currency_name, 1),
            'MedioPagos': [{'TipoMedioPago': '4'}],
        }

        tipo_venta = getattr(move, 'tipoVenta', '1') or '1'
        header['CondicionVenta'] = str(tipo_venta)
        if tipo_venta == '2':
            header['PlazoCredito'] = int(getattr(move, 'plazoVenta', '0') or 0)

        if currency_name != 'CRC':
            rate = getattr(move, 'invoice_currency_rate', 0) or 0
            if rate and rate > 0:
                header['TipoCambio'] = gti_round(1.0 / rate, self._deci)

        return {
            'NumCuenta': int(company.gti_NumCuenta),
            'Documentos': [{'Encabezado': header}],
        }

    # ═══════════════════════════════════════════════════════════════
    # RECEPTOR
    # ═══════════════════════════════════════════════════════════════
    def _build_receptor(self, move):
        partner = move.partner_id
        receptor = {'Nombre': partner.name or '', 'Correo': partner.email or ''}

        if partner.vat:
            tipo_id = getattr(partner, 'tipo_Identificacion', '') or ''
            if tipo_id:
                receptor['TipoIdent'] = int(tipo_id)
                receptor['Identificacion'] = partner.vat

        if partner.phone:
            try:
                import phonenumbers
                phone = phonenumbers.parse(
                    partner.phone, partner.country_id.code if partner.country_id else 'CR')
                receptor['AreaTelefono'] = phone.country_code or 506
                receptor['NumTelefono'] = phone.national_number or 0
            except Exception:
                pass

        email_copy = getattr(partner, 'email_copy', '') or ''
        if email_copy:
            receptor['Copia'] = email_copy

        act = getattr(move, 'receiver_economic_activity_id', None)
        if act and act.code:
            receptor['ActividadEconomica'] = act.code

        return receptor

    # ═══════════════════════════════════════════════════════════════
    # LÍNEAS — v2.0: gti_round en cada operación
    # ═══════════════════════════════════════════════════════════════
    def _build_lineas(self, move):
        """Líneas con redondeo GTI individual. Retorna datos para totales."""
        d = self._deci
        result = []

        for line in move.invoice_line_ids.filtered(
            lambda x: x.display_type not in (
                'line_note', 'line_section', 'tax', 'payment_term', 'cogs'
            ) and x.product_id
        ):
            product = line.product_id
            tmpl = product.product_tmpl_id
            qty = line.quantity or 0
            price = line.price_unit or 0
            disc_pct = line.discount or 0

            sub = gti_round(price * qty, d)
            desc_amt = gti_round(sub * disc_pct / 100.0, d) if disc_pct else 0.0
            base = gti_round(sub - desc_amt, d)

            cabys = product.cabys or tmpl.cabys or ''
            is_service = bool(cabys and str(cabys)[0] in CABYS_SERVICE_PREFIXES)

            uom_code = 1
            if line.product_uom_id and hasattr(line.product_uom_id, 'code') and line.product_uom_id.code:
                try:
                    uom_code = int(line.product_uom_id.code)
                except (ValueError, TypeError):
                    pass

            descripcion = str(tmpl.display_name or product.name or line.name or 'Producto')[:200]

            linea = {
                'Cantidad': gti_round(qty, d),
                'UnidadMedida': uom_code,
                'Descripcion': descripcion,
                'PrecioUnitario': gti_round(price, d),
                'Codigo': cabys,
            }

            if product.default_code:
                linea['CodigoComercial'] = [{'Tipo': '04', 'Codigo': str(product.default_code)[:20]}]

            if desc_amt > 0:
                disc_code = '07'
                if hasattr(line, 'discount_code_id') and line.discount_code_id:
                    disc_code = line.discount_code_id.code or '07'
                linea['Descuentos'] = [{
                    'MontoDescuento': gti_round(desc_amt, d),
                    'CodigoDescuento': disc_code,
                    'DetalleDescuento': 'Descuento comercial',
                }]

            imp_total = imp_iva = imp_otros = 0.0
            has_tax = False

            if line.tax_ids:
                impuestos = []
                for tax in line.tax_ids:
                    has_tax = True
                    pct = abs(tax.amount) if tax.amount else 0
                    monto_imp = gti_round(base * pct / 100.0, d)

                    tax_entry = {
                        'CodigoImp': 1,
                        'PorcentajeImp': gti_round(pct, d),
                        'MontoImp': monto_imp,
                    }
                    codigo_tarifa = getattr(tax, 'codigo_Imp', '') or ''
                    if codigo_tarifa:
                        tax_entry['CodigoTarifa'] = int(codigo_tarifa)

                    if tax_entry['CodigoImp'] in IVA_TAX_CODES:
                        imp_iva += monto_imp
                    else:
                        imp_otros += monto_imp
                    imp_total += monto_imp
                    impuestos.append(tax_entry)

                linea['Impuestos'] = impuestos

            result.append({
                'json': linea,
                'sub': sub, 'desc': desc_amt, 'base': base,
                'imp': gti_round(imp_total, d),
                'imp_iva': gti_round(imp_iva, d),
                'imp_otros': gti_round(imp_otros, d),
                'is_service': is_service, 'has_tax': has_tax,
            })

        return result

    # ═══════════════════════════════════════════════════════════════
    # TOTALES — v2.0: SUMA de líneas ya redondeadas
    # ═══════════════════════════════════════════════════════════════
    def _build_totales(self, lines_data):
        """Totales GTI v4.4 desde líneas ya redondeadas.
        Evita descuadres de céntimos (errores 61/62)."""
        d = self._deci
        sg = se = mg = me = td = ti_iva = ti_otros = 0.0

        for ld in lines_data:
            sub = ld['sub']
            if ld['has_tax']:
                if ld['is_service']:
                    sg += sub
                else:
                    mg += sub
            else:
                if ld['is_service']:
                    se += sub
                else:
                    me += sub
            td += ld['desc']
            ti_iva += ld['imp_iva']
            ti_otros += ld['imp_otros']

        sg, se, mg, me = gti_round(sg, d), gti_round(se, d), gti_round(mg, d), gti_round(me, d)
        td = gti_round(td, d)
        ti_iva, ti_otros = gti_round(ti_iva, d), gti_round(ti_otros, d)
        ti_total = gti_round(ti_iva + ti_otros, d)
        tg = gti_round(sg + mg, d)
        tex = gti_round(se + me, d)
        tv = gti_round(tg + tex, d)
        tvn = gti_round(tv - td, d)

        return {
            'TotalServGravado': sg, 'TotalServExento': se, 'TotalServExonerado': 0.0,
            'TotalMercaGravada': mg, 'TotalMercaExenta': me, 'TotalMercaExonerada': 0.0,
            'TotalGravado': tg, 'TotalExento': tex, 'TotalExonerado': 0.0,
            'TotalVenta': tv, 'TotalDescuento': td, 'TotalVentaNeta': tvn,
            'TotalImpuesto': ti_total, 'TotalImpVenta': ti_iva, 'TotalImpOtros': ti_otros,
            'TotalIVADevuelto': 0.0, 'TotalOtrosCargos': 0.0,
            'TotalComprobante': gti_round(tvn + ti_total, d),
        }

    # ═══════════════════════════════════════════════════════════════
    # REFERENCIA NC/ND — v2.0: NC parciales
    # ═══════════════════════════════════════════════════════════════
    def _build_referencia(self):
        """Referencia con auto-detección NC parcial vs total."""
        user_tz = pytz.timezone(self.env.company.tz or 'America/Costa_Rica')

        doc_original = self.env['documento.hacienda'].sudo().search([
            ('factura', '=', self.factura.id),
            ('consecutivo', '!=', False), ('codigo', '=', '0'),
        ], limit=1)

        if not doc_original:
            raise UserError(_(
                'No se encontró el documento original emitido. '
                'Verifique que la factura original fue enviada a GTI.'))

        monto_orig = abs(self.factura.amount_total) if self.factura else 0
        monto_nc = abs(self.factura_NC.amount_total) if self.factura_NC else 0

        if monto_orig > 0 and abs(monto_nc - monto_orig) < 0.01:
            accion, razon = 1, 'Anula documento de referencia'
        else:
            accion, razon = 3, 'Nota de crédito parcial - Corrige montos'

        fecha_ref = doc_original.fecha_Emsion
        if fecha_ref:
            fecha_str = fecha_ref.astimezone(user_tz).strftime('%Y-%m-%dT%H:%M:%S')
        else:
            fecha_str = (self.factura.invoice_date or datetime.now().date()).isoformat()

        return {
            'TipoDocRef': int(doc_original.tipo),
            'NumeroRef': doc_original.consecutivo,
            'FechaRef': fecha_str,
            'AccionRef': accion,
            'RazonNota': razon,
        }

    # ═══════════════════════════════════════════════════════════════
    # DESCARGA PDF — v2.0: NUEVO
    # ═══════════════════════════════════════════════════════════════
    def descargar_pdf(self):
        """Descargar PDF de GTI y adjuntar al chatter."""
        self.ensure_one()
        if not self.consecutivo:
            raise UserError(_('No hay consecutivo. Primero emita el documento.'))

        move = self.factura or self.factura_NC or self.factura_ND
        company = move.company_id if move else self.company_id
        url = '%s/Documentos/ObtenerBytesPdfEmision' % company.gti_url

        try:
            response = requests.get(url, params={
                'numCuenta': company.gti_NumCuenta,
                'consecutivo': self.consecutivo,
                'usuario': company.gti_Usuario,
                'clave': company.gti_Clave,
            }, timeout=30, verify=False)
        except Exception as e:
            raise UserError(_('Error al descargar PDF: %s') % str(e))

        if response.status_code != 200 or not response.content or len(response.content) < 50:
            raise UserError(_(
                'PDF no disponible aún. GTI necesita 1-5 min después de emisión. Reintente.'))

        text = response.content.decode('utf-8', errors='replace').strip()
        b64 = None

        if text.startswith('{'):
            try:
                data = json.loads(text)
                if int(data.get('Codigo', 0) or 0) != 1:
                    raise UserError(_('GTI no pudo generar el PDF: %s') % data.get('Mensaje', ''))
                b64 = str(data.get('Datos', data.get('datos', ''))).strip().strip('"')
            except (ValueError, KeyError):
                pass

        if not b64:
            if text.startswith('JVBER'):
                b64 = text
            elif text.startswith('%PDF'):
                b64 = base64.b64encode(text.encode('latin-1')).decode()

        if not b64:
            raise UserError(_('Formato de PDF no reconocido.'))

        try:
            if base64.b64decode(b64)[:4] != b'%PDF':
                raise UserError(_('Archivo descargado no es PDF válido.'))
        except Exception:
            raise UserError(_('Error decodificando PDF.'))

        fn = 'FE_%s.pdf' % self.consecutivo

        att = self.env['ir.attachment'].create({
            'name': fn, 'type': 'binary', 'datas': b64,
            'res_model': self._name, 'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        self.message_post(
            body=Markup('<strong>📄 %s</strong>') % _('PDF descargado'),
            attachment_ids=[att.id])

        if move:
            att2 = self.env['ir.attachment'].create({
                'name': fn, 'type': 'binary', 'datas': b64,
                'res_model': 'account.move', 'res_id': move.id,
                'mimetype': 'application/pdf',
            })
            move.message_post(
                body=Markup(
                    '<div style="background:#e8f5e9;border:1px solid #4caf50;'
                    'border-radius:4px;padding:8px;">'
                    '<strong style="color:#2e7d32;">📄 PDF Factura Electrónica'
                    '</strong></div>'),
                attachment_ids=[att2.id])

        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {'title': _('PDF Descargado'),
                'message': _('PDF adjunto en el chatter de la factura.'),
                'type': 'success', 'sticky': False},
        }
