# -*- coding: utf-8 -*-
import json
import pytz
import requests
import phonenumbers
import logging
from datetime import date, timedelta, datetime
from odoo import api, fields, models,_
from odoo.exceptions import UserError
from odoo.addons.website.tools import text_from_html

_logger = logging.getLogger(__name__)


class DocumentoHacienda(models.Model):
    _name = "documento.hacienda"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Información de los Documentos de Hacienda"
    _order = 'consecutivo'


    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )

    activo = fields.Boolean(
        string="Activo",
        default=True,
        tracking=True,
    )

    clave = fields.Char(
        string="Clave",
        required=False,
        tracking=True,
    )

    fecha_Emsion = fields.Datetime(
        string="Fecha Emisión",
        required=False,
        tracking=True,
    )

    consecutivo = fields.Char(
        string="Consecutivo",
        required=False,
        tracking=True,
    )

    consecutivo_Interno = fields.Char(
        string="Consecutivo GTI",
        required=False,
        tracking=True,
    )

    tipo = fields.Selection(
        string="Tipo",
        selection=[
            ("1", "Factura Electrónica"),
            ("2", "Nota de Débito Electrónica"),
            ("3", "Nota de Crédito Electrónica"),
            ("4", "Tiquete Electrónico"),
            ("5", "Confirmación de Aceptación del Comprobante Electrónico"),
            ("6", "Confirmación de Aceptación Parcial del Comprobante Electrónico"),
            ("7", "Confirmación de Rechazo del Comprobante Electrónico"),
            ("8", "Factura Electrónica de Compra"),
            ("9", "Factura Electrónica de Exportación"),
            ("10", "Recibo Electrónico de Pago"),
        ],
        required=True,
        tracking=True,
    )

    codigo = fields.Selection(
        string="Estado",
        selection=[
            ('0', 'Exitoso La emisión de documentos fue exitosa'),
            ('1', 'Falta información requerida en Encabezado. No se ha indicado el apartado (Encabezado) del documento.'),
            ('2', 'Configuración no permitida con los decimales. La cantidad de decimales (CantDeci) configurada no concuerda con lo permitido.'),
            ('3', 'Error en tipo de documento. No se ha indicado ningún valor válido en (TipoDoc).'),
            ('4', 'Error en situación de envío. No se ha indicado ningún valor válido en (SituacionEnvio).'),
            ('5', 'Combinación de datos incorrecta. La combinación de (TipoDoc) con (SituacionEnvio) no es permitida.'),
            ('6', 'Error en fecha del documento. El valor de (FechaFactura) no es válido, sobre pasa la fecha actual.'),
            ('7', 'Combinación de datos incorrecta. El valor de (FechaFactura) para la (SituacionEnvio) sobrepasa los límites.'),
            ('8', 'Error en Moneda del documento. No se ha indicado ningún valor válido en (Moneda).'),
            ('9', 'Error en Tipo Cambio del documento. Valor o cantidad de decimales inválido en (TipoCambio).'),
            ('10', 'Error en apartado Medios de Pago. No se han indicado valores validos en el apartado Medio de pago.'),
            ('11', 'Error en el campo FechaRef del apartado Referencia. La fecha indicada en (FechaRef) no entra el rango permitido.'),
            ('12', 'Error en Condición de Venta. No se ha indicado ningún valor válido en (CondicionVenta).'),
            ('13', 'Error en Plazo de Crédito. No se ha indicado ningún valor válido en (PlazoCredito) según la condición de venta.'),
            ('14', 'Error en Nombre Receptor. No hay un valor que cumpla con lo establecido en Receptor (Nombre).'),
            ('15', 'Error en Nombre Comercial Receptor. No hay un valor que cumpla con lo establecido en Receptor (NombreComercial).'),
            ('16', 'Error en Identificación Receptor. La Identificación Receptor no cumplen lo establecido (TipoIdent) y (Identificacion).'),
            ('17', 'Error en Teléfono Receptor. El Teléfono del Receptor no cumple lo establecido (AreaTelefono) y el (NumTelefono).'),
            ('18', 'Error en Fax Receptor. El Fax del Receptor no cumple lo establecido (AreaFax) y el (NumFax).'),
            ('19', 'Error en Dirección Receptor. No hay un valor que cumpla con lo establecido en Receptor (Direccion).'),
            ('20', 'Error en la Ubicación del Receptor. Combinación de Receptor (Provincia) (Canton) (Distrito) es inválida.'),
            ('21', 'Error en Ubicación Barrio Receptor. La Ubicación del Receptor no cumple lo establecido en el (Barrio).'),
            ('22', 'Error en Correo Receptor. El Correo del Receptor no cumple con el formato establecido en el(Correo).'),
            ('23', 'Error en Líneas Detalle. No se ha indicado ninguna línea de detalle (Lineas).'),
            ('24', 'Error en Cantidad Líneas Detalle. Se excede el número máximo de líneas permitidas (Lineas).'),
            ('25', 'Error en Tipo Línea Detalle. No se ha indicado ningún valor válido en Línea (Tipo).'),
            ('26', 'Error en Códigos, Línea. Los cantidad de códigos para la línea no concuerdan el (CodTipo) y el(CodProdServ).'),
            ('27', 'Error en Código Tipo Producto, Línea. Se ha indicado un valor inválido en la Línea (CodTipo).'),
            ('28', 'Error en Códigos, Línea. Un valor para código producto/servicio no cumple con lo establecido (CodProdServ).'),
            ('29', 'Error en Unidad Medida, Línea. No se ha indicado ningún valor válido en (UnidadMedida) de la linea.'),
            ('30', 'Error en Cantidad, Línea. El Campo (Cantidad) de la línea es inválido o no concuerdan sus decimales.'),
            ('31', 'Error en Descripción, Línea. El Campo (Descripcion) de la línea no cumple con el formato establecido.'),
            ('32', 'Error en Precio Unitario, Línea. El (PrecioUnitario) de la línea no cumple con el formato establecido o tiene una configuración de decimales inválida.'),
            ('33', 'Error en Monto Descuento, Línea. El (Descuento) de la línea no cumple con el formato establecido o tiene una configuración de decimales inválida.'),
            ('34', 'Error en Detalle Descuento, Línea. El Campo (DetalleDescuento) de la línea no cumple con el formato establecido.'),
            ('35', 'Error en Repetición Impuestos, Línea. En las líneas de detalle no puede utilizar dos impuestos de un mismo Codigo'),
            ('36', 'Error en Código Impuesto, Línea. El (CodigoImp) de la línea no se colocó o su valor es incorrecto.'),
            ('37', 'Error en Tipo Doc Exoneración, Línea. El (TipoDocExo) de la línea no se colocó o su valor es invalido.'),
            ('38', 'Combinación inválida Impuesto Exoneración, Línea. La exoneración solo puede aplicarse para el impuesto IVA tradicional, código 1.'),
            ('39', 'Error en Número Exoneración, Línea. El (NumeroExoneracion) no se colocó o es invalido.'),
            ('40', 'Error en Institución Exoneración, Línea. El (NombreInstitucion) de la línea no se colocó o su valor es inválido.'),
            ('41', 'Error en Fecha Exoneración, Línea. La (FechaExoneracion) no se colocó o su valor es inválido.'),
            ('42', 'Error en Porcentaje Exoneración, Línea. El (PorcentajeExonerado) de la línea no se colocó o su valor es invalido.'),
            ('43', 'Error en Monto Exoneración de la Línea. El (MontoExonerado) de la línea no se colocó o su valor es invalido.'),
            ('44', 'Combinación Impuesto con Exoneración, Línea. La combinación de impuesto con exoneración es inválida.'),
            ('45', 'Error en Porcentaje Impuesto, Línea. El (PorcentajeImpuesto) de la línea no se colocó o es invalido.'),
            ('46', 'Error en Monto Impuesto, Línea. El (MontoImpuesto) de la línea no se colocó o es invalido.'),
            ('47', 'El descuento supera el total, Línea. El (Descuento) supera el precio bruto de la línea. El precio bruto se saca multiplicando la cantidad por el precio unitario.'),
            ('48', 'Error de cálculo Monto Impuesto Otros, Línea. El (MontoImpuesto) de la línea contiene un cálculo incorrecto.'),
            ('49', 'Error de cálculo Monto Impuesto del Valor Agregado, Línea. Error de cálculo Monto Impuesto del Valor Agregado, Línea. El (MontoImpuesto) de la línea contiene un cálculo incorrecto.'),
            ('50', 'No se ha indicado apartado de Totales No se ha colocado los (Totales) en el documento.'),
            ('51', 'Los Totales exceden el máximo establecido En los totales del documento sobrepasan la cantidad de decimales establecida.'),
            ('52', 'Monto Servicio Gravado incorrecto, Totales El (TotalServGravados) no se colocó o su valor es inválido según la configuración establecida.'),
            ('53', 'Monto Servicio Exento incorrecto, Totales El (TotalServExento) no se colocó o su valor es inválido según la configuración establecida.'),
            ('54', 'Monto Mercancia Gravada incorrecto, Totales El (TotalMercaGravada) no se colocó o su valor es inválido según la configuración establecida.'),
            ('55', 'Monto Mercancia Exenta incorrecto, Totales El (TotalMercaExenta) no se colocó o su valor es inválido según la configuración establecida.'),
            ('56', 'Monto Total Gravado incorrecto, Totales El (TotalGravado) no se colocó o su valor es inválido según la configuración establecida.'),
            ('57', 'Monto Total Exento incorrecto, Totales El (TotalExento) no se colocó o su valor es inválido según la configuración establecida.'),
            ('58', 'Monto Total Venta incorrecto, Totales El (TotalVenta) no se colocó o su valor es inválido según la configuración establecida.'),
            ('59', 'Monto Total Descuento incorecto, Totales El (TotalDescuento) no se colocó o su valor es inválido según la configuración establecida.'),
            ('60', 'Monto Total Venta Neta incorrecto, Totales El (TotalVentaNeta) no se colocó o su valor es inválido según la configuración establecida.'),
            ('61', 'Monto Total Impuesto incorrecto, Totales El (TotalImpuesto) no se colocó o su valor es inválido según la configuración establecida.'),
            ('62', 'Monto Total Comprobante incorrecto, Totales El (TotalComprobante) no se colocó o su valor es inválido según la configuración establecida.'),
            ('63', 'Tipo Doc Referencia inválido, Referencia El (TipoDocRef) no se colocó o su valor es inválido.'),
            ('64', 'Acción de Referencia inválida, Referencia El (AccionRef) no se colocó o su valor es inválido.'),
            ('65', 'Razón de Referencia inválida, Referencia El (RazonRef) no se colocó o su valor es inválido.'),
            ('66', 'Combinación de Referencia inválida, Referencia La combinación establecida con (TpoDocRef) y (AccionRef) en referencia es inválida.'),
            ('67', 'La Referencia es requerida para el tipo de documento La referencia es requerida para las facturas con situación de envió por contingencia, tiquetes con situación de envió por contingencia, notas de crédito o notas de débito.'),
            ('68', 'Consecutivo de referencia no existe en BD, Referencia El número de referencia al que le desea aplicar la nota no se encuentra registrado en el sistema. '),
            ('69', 'Combinación Terminal, Sucursal no configurada. La combinación de la sucursal y terminal según su cuenta es inválida.'),
            ('70', 'Error en Consecutivo indicado por cliente. El consecutivo enviado por el cliente es  inválido según la estructura establecida.'),
            ('71', 'Error en Clave Numérica indicada por cliente. La clave numérica enviada por el cliente es inválida según la estructura establecida.'),
            ('72', 'Error Clave Numérica ya existe en BD La clave numérica enviada por el cliente ya se encuentra registrada.'),
            ('73', 'Error Nombre Comercial Emisor, Dinámico El (NombComercial) colocado en el Emisor excede la cantidad de caracteres permitidos.'),
            ('74', 'Error Número Referencia de Contingencia El (NumeroRef) colocado en el Emisor excede la cantidad establecida.'),
            ('75', 'Error en Clave Referencia Externa La (ClaveNumRef) es inválida segun la estructura establecida'),
            ('76', 'Error en Unidad Medida Comercial, Línea La (UnidadComercial) es inválida según la estructura establecida.'),
            ('90', 'Error al Agregar Línea Detalle. Error al agregar la línea de detalle, comuníquese con el administrador.'),
            ('91', 'Error al Generar XML Hacienda Error al generar el XML que debe ser enviado a Hacienda, comuníquese con el administrador.'),
            ('92', 'Error al Generar Firma Digital Error al generar la firma digital, comuníquese con el administrador.'),
            ('93', 'Error al Emitir Documento Error al guardar el documento, comuníquese con el administrador.'),
            ('94', 'Error al Guardar Clave Numérica Error al guardar el documento, comuníquese con el administrador. '),
            ('99', 'Error interno en el proceso Comuníquese con el administrador.'),
            ('100', 'Error en código de actividad económica No se ha indicado ningún valor válido en (CodigoActividad).'),
            ('101', 'Error en Receptor No se ha indicado ningún valor (Receptor) y este es requerido para el tipo de documento 1 (Factura Electrónica) y 8 (Factura Electrónica de Compra).'),
            ('102', 'Error en Partida Arancelaria, Línea La (PartidaArancelaria) de la línea no cumple con el formato establecido o no existe.'),
            ('103', 'Error en Codigo, Línea. El campo no cumple con el formato establecido o no existe. El código Cabys es un número de 13 dígitos que debe existir en el catálogo de Hacienda. Además, es un valor obligatorio a partir del 01 de diciembre de 2020 para los productos y servicios.'),
            ('104', 'Error en Descuentos, Línea Los (Descuentos) de la línea no cumple con el formato establecido o excede el máximo permitido.'),
            ('105', 'Error en Base Imponible, Línea La (BaseImponible) de la línea no cumple con el formato establecido o tiene una configuración de decimales inválida.'),
            ('106', 'Error en Base Imponible, Línea La (BaseImponible) es obligatoria para el impuesto IVA (cálculo especial)'),
            ('107', 'Error en Otros Cargos La cantidad de lineas de OtrosCargos excede el máximo permitido.'),
            ('108', 'Error en Tipo de documento, Otros Cargos No se ha indicado ningún valor válido en (TipoDoc).'),
            ('109', 'Error en Número Identidad Tercero, Otros Cargos El campo Identidad Tercero es obligatorio para el OtrosCargos->TipoDocumento 4.'),
            ('110', 'Error en Número Identidad Tercero, Otros Cargos El campo (NumeroIdentidadTercero) no tiene un valor válido según la configuración establecida.'),
            ('111', 'Error en Nombre Tercero, Otros Cargos El campo (NombreTercero) no tiene un valor válido según la configuración establecida.'),
            ('112', 'Error en Detalle, Otros Cargos El campo (Detalle) no tiene un valor válido según la configuración establecida.'),
            ('113', 'Error en Porcentaje, Otros Cargos El (Porcentaje) no se colocó o su valor es inválido según la configuración establecida.'),
            ('114', 'Error en Monto Cargo, Otros Cargos El (MontoCargo) no se colocó o su valor es inválido según la configuración establecida.'),
            ('115', 'Error en Nombre Tercero, Otros Cargos El (NombreTercero) es obligatorio para el OtrosCargos->TipoDocumento 4.'),
            ('116', 'Error en Numero Identidad Tercero, Otros Cargos La Identificación no cumplen con la configuración establecida.'),
            ('117', 'Error en Código Tarifa, Impuestos El (CodigoTarifa) es obligatorio para el impuesto 1 (Impuesto al Valor Agregado) y 7 (IVA).'),
            ('118', 'Error en Código Tarifa, Impuestos El (CodigoTarifa) no tiene un valor válido según la configuración establecida.'),
            ('119', 'Error en Factor IVA, Impuestos El (FactorIVA) es obligatorio para el impuesto 8 (IVA Régimen de Bienes Usados).'),
            ('120', 'Error en Factor IVA, Impuestos El campo (FactorIVA) no tiene un valor válido según la configuración establecida.'),
            ('121', 'Error en Monto Exportacion, Impuestos El (MontoExportación) es obligatorio para el tipo de documento 9 (Factura Electrónica de Exportación).'),
            ('122', 'Error en Monto Exportación, Impuestos El campo (MontoExportacion) no tiene un valor válido según la configuración establecida.'),
            ('123', 'Monto Servicio Exonerado incorrecto, Totales El (TotalServExonerado) no se colocó o su valor es inválido según la configuración establecida.'),
            ('124', 'Monto Mercancia Exonerada incorrecto, Totales El (TotalMercaExonerada) no se colocó o su valor es inválido según la configuración establecida.'),
            ('125', 'Monto Total Exonerado incorrecto, Totales El (TotalExonerado) no se colocó o su valor es inválido según la configuración establecida.'),
            ('126', 'Monto Total Otros Cargos incorrecto, Totales El (TotalOtrosCargos) no se colocó o su valor es inválido según la configuración establecida.'),
            ('127', 'Monto Total IVA Devuelto incorrecto, Totales El (TotalIVADevuelto) no se colocó o su valor es inválido según la configuración establecida.'),
            ('128', 'Error al Agregar Línea Otros Cargos. Error al agregar la línea de Otros Cargos, comuníquese con el administrador.'),
            ('130', 'Error de cálculo Monto Exonerado, Exoneración. El (MontoExonerado) de la línea contiene un cálculo incorrecto.'),
            ('131', 'Error de cálculo Monto Exonerado, Exoneración. El (MontoExonerado) no puede ser mayor al (MontoImp) de la línea.'),
            ('132', 'Error en Codigo, Impuestos Solo se puede colocar un tipo de IVA(cód. 1, cód. 7 o cód.8).'),
            ('133', 'Error en Identificación Receptor. Para la factura electrónica y factura electrónica de compra no se permite la identificación extranjera cód. 10 (solo puede facturar a receptores que se encuentren inscritos ante Hacienda.'),
            ('134', 'Error en Receptor La información del receptor: nombre, identificación, ubicación, teléfono y correo electrónico es requerido para el tipo de documento 1 (Factura Electrónica) y 8 (Factura Electrónica de Compra).'),
            ('135', 'Error en Exoneración No se puede exonerar productos o servicios que contengan un impuesto con tarifa cód. 1 (Exenta) y cód 5 (Transitorio 0%).'),
            ('136', 'Error en Impuestos El IVA Devuelto no aplica para facturas de compras cód. 8 y exportación cód.9.'),
            ('137', 'Error en Exoneración La exoneración no aplica para facturas de exportación cód.9.'),
            ('138', 'Error en Líneas Detalle. La base imponible no aplica para facturas de exportación cód.9.'),
            ('139', 'Error en Referencia El número de referencia al que le desea aplicar la nota no se encuentra registrado en el sistema.'),
            ('141', 'Error en el apartado de la exoneración. Para las exoneraciones es requerido que el comprobante electrónico posea la información del receptor.'),
            ('142', 'Error en el apartado de la exoneración. El (PorcentajeExonerado) no puede ser mayor al (PorcentajeImp) o al porcentaje según el (CodigoTarifa) del impuesto.'),
            ('143', 'Número interno duplicado Número interno duplicado'),
            ('144', 'Error RegistroMedicamento y FormaFarmaceutica Error en los campos RegistroMedicamento y FormaFarmaceutica, deben de llenarse'),
            ('145', 'No existe el código forma farmacéutica No existe el código forma farmacéutica'),
            ('146', 'Error en NumeroFactura El campo (NumeroFactura) no tiene un valor válido según la configuración establecida.'),
            ('147', 'Error Identificación Receptor Obligatorio La identificación del Receptor es obligatorio para la Factura de exportación.'),
            ('148', 'Error en Condición Venta de referencia La condición de venta (Pago de servicios prestado al Estado) se utilizará únicamente para (Servicios prestados al Estado)'),
            ('149', 'Error en Condición Venta de referencia La condición de venta (Pago de venta a crédito en IVA hasta 90 días) se utilizará únicamente para (Venta a crédito en IVA hasta 90 días)'),
            ('150', 'Error en Impuestos Los Impuestos son obligatorios'),
            ('151', 'Error en Actividad económica del receptor en factura de compra Error en Actividad económica del receptor en factura de compra'),
            ('152', 'Error código de actividad económica del receptor inválido Error código de actividad económica del receptor inválido'),
            ('153', 'Error en Tipo de documento de referencia OTRO No se ha indicado ningún valor válido en (TipoDocRefOTRO)'),
            ('154', 'Error en el campo Registro Fiscal 8707, máximo permitido 12 caracteres Error en el campo Registro Fiscal 8707, máximo permitido 12 caracteres'),
            ('155', 'Error en cedula Extranjero No Domiciliado El tipo de cedula Extrajero No Domiciliado es válido para las Facturas de Compra'),
            ('156', 'Error en la Identificación La identificación excede la longitud permitida'),
            ('157', 'Error en cedula Extranjero No Domiciliado El tipo de documento no es permitido para la cedula Extranjero No Domiciliado'),
            ('158', 'Error en Condicion de Venta El campo de Condición de venta no válido para la Factura electrónica y cedula Extrajero No Domiciliado'),
            ('159', 'Error en OtrasSenas Extranjero El campo (OtrasSenasExtranjero) no se colocó o su valor en inválido'),
            ('160', 'Error en Tipo de documento de referencia El campo (TipoDocRef) con valor Comprobante de Proveedor No Domiciliado es válido solo para la Factura de Compra'),
            ('161', 'Error en Referencia El nodo referencia es obligatorio para la factura con la cedula Extranjero No Domiciliado'),
            ('162', 'Error en tipo de identificación receptor Para la Factura Electrónica de Compra y condición de venta Venta Bienes Usados No Contribuyente, el tipo de identificación debe ser No Contribuyente'),
            ('163', 'Error en Tipo de documento OTROS El campo (TipoDocOtros) no se colocó o su valor en inválido'),
            ('164', 'Error en Tipo de identificación tercero El campo (TipoIdTercero) no se colocó o su valor en inválido'),
            ('165', 'IdentificacionNoContribuyenteNoEsValido La identificación del receptor no contribuyente no es válida.'),
            ('166', 'Condicion de venta bienes usados no valido La condición de venta bienes usados es valido solo para facturas de compra'),
            ('167', 'Error Tipo Transacción No Aplicable El tipo de transacción no es aplicable a este documento'),
            ('168', 'Error Tipo Transacción Formato El tipo de transacción debe ser de 2 dígitos'),
            ('169', 'Error Tipo Transacción No Existe El tipo de transacción no existe'),
            ('170', 'Error IVA Cobrado en Fábrica no Aplicable El IVA cobrado en fábrica no es aplicable a este documento'),
            ('171', 'Error IVA Cobrado Formato El IVA cobrado debe ser de 2 dígitos'),
            ('172', 'Error Impuesto Asumido Mayor a Zero El impuesto asumido por el emisor fábrica debe ser mayor a zero'),
            ('173', 'Error Impuestos Nulos o Vacíos Los impuestos no pueden ser nulos o vacíos'),
            ('174', 'Error Impuesto IVA No Existe El impuesto IVA no existe'),
            ('175', 'Error Impuesto IVA No Exento El impuesto IVA no puede ser exento'),
            ('177', 'Error Impuesto IVA Exento No Existe El impuesto IVA exento no existe'),
            ('178', 'Error Impuesto Asumido Fábrica no Aplicable El impuesto asumido por emisor fábrica no es aplicable a este documento'),
            ('179', 'Error Necesario Descuento, Regalia o Bonificación Es necesario tener descuento, regalía o bonificación e impuesto para cemento, bebidas alcohólicas o bebidas sin alcohol'),
            ('180', 'Error Impuesto Asumido Formato o Decimales El impuesto asumido por emisor fábrica no cumple el formato establecido o decimales'),
            ('181', 'Error Impuesto Asumido Diferente de Monto El impuesto asumido por el emisor fábrica no es igual al monto de impuestos'),
            ('182', 'Error Impuesto Asumido Requerido El impuesto asumido por emisor fábrica es requerido'),
            ('183', 'Error Total Impuesto Asumido Inválido El total del impuesto asumido en fábrica es inválido'),
            ('184', 'Error en Codigo Descuento El campo (CodigoDescuento) no se colocó o su valor en inválido'),
            ('185', 'Error en Codigo Descuento Otros El campo (CodigoDescuentoOTROS) no se colocó o su valor en inválido'),
            ('186', 'Error en en el campo Barrio Receptor El campo (NombreBarrio) es inválido, mínimo 5, máximo 50 caracteres'),
            ('187', 'Error en en el campo Barrio Emisor El campo (NombreBarrio) es inválido, mínimo 5, máximo 50 caracteres'),
            ('188', 'Error TotalComprobante y MedioPago El total de comprobante y el total de medio de pago no coinciden'),
            ('189', 'Error TotalIVADevuelto y MedioPago El total IVA Devuelto se utiliza para medio de pago tarjeta y s CABy´S de servicios médicos'),
            ('190', 'Error en base imponible La base imponible no aplica para Facturas de Exportación (cód.9)'),
            ('191', 'Error en base imponible La base imponible no aplica para Recibos de Pago (cód. 10)'),
            ('192', 'Error en Base Imponible, Línea El nodo (BaseImponible) es obligatorio para los códigos de impuesto 07 (IVA Especial), o para el IVA Cobrado de Fabrica (codigo 01)'),
            ('193', 'Error Código Tarifa Transitori 8% solo para Nota Crédito o Débito'),
            ('194', 'Error Tarifa Impuesto Para el Impuesto al Cemento la Tarifa colocada es inválida'),
            ('195', 'Error Total Medio de Pago El campo TotalMedioPago no se colocó o es inválido'),
            ('196', 'Error Exoneración Articulo El campo Articulo de Exoneración no se colocó o es inválido'),
            ('197', 'Error Exoneración Inciso El campo Inciso de Exoneración no se colocó o es inválido'),
            ('198', 'Error Exoneracion Nombre Institución. El campo (NombreInstitucion) no se ha indicado o tiene una longitud incorrecta (2 caracteres).'),
            ('199', 'Error Exoneracion Nombre Institución. El (NombreInstitucion) indicado no se encuentra en el catalogo de Nombre Institucion suministrado por el Ministerio de Hacienda.'),
            ('300', 'CantidadLineasSurtidoSuperaLimite Se excede el límite de líneas de surtido.'),
            ('301', 'IVACobradoFabricaNoAplicableAEsteDocumentoSurtido IVA cobrado de fábrica no aplica para este documento de surtido.'),
            ('302', 'IVACobradoDebeSerDe2DigitosSurtido El IVA cobrado de surtido debe usar 2 dígitos.'),
            ('303', 'ImpuestosNoPuedenSerNulosOVaciosSurtido No se permiten impuestos nulos o vacíos en surtido.'),
            ('304', 'ImpuestoIVANoExisteSurtido El impuesto IVA usado en surtido no existe.'),
            ('305', 'ImpuestoIVANoPuedeSerExentoSurtido No se puede asignar exento a IVA en surtido.'),
            ('306', 'PorcentajeSurtidoEnImpuestoEspecificoNoValido El porcentaje en impuesto específico es inválido.'),
            ('307', 'ProporcionSurtidoEnImpuestoEspecificoNoValido La proporción indicada en impuesto específico es incorrecta.'),
            ('308', 'ImpuestoUnidadImpuestoEspecificoNoValido La unidad de impuesto específico no es válida.'),
            ('309', 'PorcentajeSurtidoDecimalesNoValidos El porcentaje de surtido contiene decimales inválidos.'),
            ('310', 'ProporcionSurtidoNoEsIgualACantidadUnidadMedidaPorPorcentajeSurtido La proporción difiere de la cantidad esperada.'),
            ('311', 'MontoImpuestoDeImpuestoEspecificoNoEsValido El monto de impuesto específico no es válido.'),
            ('312', 'MontoImpuestoDeImpuestoEspecificoNoEsIgualCantidadUnidadMedidaPorProporcionSurtidoPorImpuestoUnidad El monto no coincide con la unidad e impuesto configurados.'),
            ('313', 'CantidadUnidadMedidaEnImpuestoEspecificoNoEsValido La cantidad de unidad de medida es inválida.'),
            ('314', 'VolumenUnidadConsumoEnImpuestoEspecificoNoEsValido El volumen de unidad de consumo es inválido.'),
            ('315', 'MontoImpuestoDeImpuestoEspecificoNoEsIgualACantidadPorCantidadUnidaMedidaPorImpuestoUnidadEntreVolum El monto final no coincide con el cálculo esperado.'),
            ('316', 'MontoImpuestoEspecificoNoEsIgualACantidadUnidadMedidaPorImpuestoUnidad El monto difiere de la fórmula base de impuesto específico.'),
            ('317', 'CodigoImpuestoOtroEsInvalido El código para otro impuesto es inválido.'),
            ('318', 'MontoImpuestoDeImpuestoEspecificoNoEsIgualACantidadPorImpuestoUnidad El monto no coincide con la unidad de impuesto configurada.'),
            ('319', 'LineasDetalleSonRequeridasConLaCombinacionOtrosCargos Se requieren líneas de detalle con esta combinación de otros cargos.'),
            ('320', 'NoExisteLineaServicioGravadoConIVA No se encontró línea de servicio gravado con IVA.'),
            ('321', 'NoExisteLineaServicioGravadoExentasIVA No se encontró línea de servicio exenta de IVA.'),
            ('322', 'NoExisteLineaServicioConExoneracion No se encontró línea de servicio con exoneración.'),
            ('323', 'TotalServicioNoSujetoIncorrecto El total de servicio no sujeto se calculó de forma incorrecta.'),
            ('324', 'NoExisteLineaServicioNoSujeto No se encontró línea de servicio no sujeto.'),
            ('325', 'TipoExoneracionOTROInvalido El tipo de exoneración “OTRO” es inválido.'),
            ('326', 'Error Exoneracion Nombre Institución Otros. El campo (NombreInstitucionOtros) es obligatorio cuando se utiliza el NombreInstitucion igual a Otros (cód 99).'),
            ('327', 'Error en Condición de venta Otros Error en el campo de condición de venta Otros'),
            ('328', 'Error Exoneracion Nombre Institución Otros. El campo (NombreInstitucionOtros) debe tener una longitud entre 6 y 160 caracteres.'),
            ('329', 'NoExisteLineaMercaNoSujeto No se encontró línea de mercancía no sujeta.'),
            ('330', 'Error Codigo de Referencia Otro El campo (CodigoReferenciaOTRO) tiene un valor inválido, debe ser entre 5 o 100 caracteres'),
            ('331', 'Error en Referencia El nodo referencia es obligatorio para la Factura Electrónica de Compra, Nota de Crédito Electrónica, Nota de Débito Electrónica, Recibo Electrónico de Pago y Factura Electrónica con exoneracion tipo documento 11'),
            ('332', 'Error en el campo Numero VINoSerie El campo (VINoSerie) debe tener una longitud menor a 17 caracteres.'),
            ('333', 'CantidadCodigosComercialExcedeLimite La cantidad de códigos comerciales excede el máximo permitido.'),
            ('334', 'TipoCodigoComercialNoEstaEnCatalogo El tipo de código comercial no se encuentra en el catálogo.'),
            ('335', 'LaCantidadDeCaracteresDelCodigoComercialNoEsValida La longitud del código comercial es inválida.'),
            ('336', 'UnidadMedidaNoEsValida La unidad de medida especificada no es válida.'),
            ('337', 'Error en TotalNoSujeto El campo TotalNoSujeto tiene un valor inválido.'),
            ('338', 'Error en Nodo Otros En el nodo de Otros los campos "OtroTexto" o "OtroContenido" tienen un valor inválido.'),
            ('339', 'CantidadNoValida La cantidad especificada es inválida.'),
            ('340', 'DetalleNoValido El detalle especificado no es válido.'),
            ('341', 'PrecioUnitarioNoValido El precio unitario no es válido.'),
            ('342', 'CantidadDescuentosNoValido La cantidad de descuentos es inválida.'),
            ('343', 'MontoDescuentoNoValido El monto de descuento es inválido.'),
            ('344', 'CodigoDescuentoNoValido El código de descuento no es válido.'),
            ('344', 'CodigoDescuentoNoValido El código de descuento no es válido.'),
            ('345', 'UnidadMedidaComercialNoEsValida La unidad de medida comercial no es valida.'),
            ('346', 'CodigoCABYSNoEsValido El código CABYS indicado no es valido'),
            ('347', 'Error Base Imponible Debe indicar el valor para la Base Imponible (Lineas)'),
            ('348', 'Error Total Mercancia NoSujeto Invalido en los decimales del total mercancia NoSujeto'),
            ('349', 'Error subtotal no es igual total de surtidos El subtotal de la linea debe ser igual al subtotal de los componentes de surtido por la cantidad de la linea'),
            ('350', 'Monto impuesto surtido invalido El monto impuesto del surtido no es correcto, de acuerdo a las indicaciones del Ministerio de Hacienda'),
            ('351', 'Descuentos no debe estar presente Cuando utiliza surtidos, los descuentos no deben estar presente para el nodo de la linea'),
            ('352', 'Codigo comercial requerido Al utilizar codigo cabys de surtido, es obligatorio indicar Codigo Comercial'),
            ('353', 'Tipo codigo comercial requerido Tipo codigo comercial es requerido'),
            ('354', 'Tipo codigo comercial debe ser Industria El tipo codigo comercial cuando usa cabys surtido debe ser 3(Codigo Industria)'),
            ('355', 'Exoneracion No Valida Cuando una linea contiene surtidos, la linea no puede contener exoneracion'),
            ('356', 'Transitorio 0% solo para NC/ND El código de tarifa Transitorio 0% [05] solo es aplicable a ND/NC'),
            ('357', 'Impuesto IVA Cobrado Fabrica 2 Solo puede existir un solo impuesto, y debe ser exento para [IVA Cobrado Fabrica](02)'),
            ('358', 'IVA Factor No Valido El IVA Factor no es valido para surtidos'),
            ('359', 'Monto Impuesto Surtido No Valido El monto del impuesto del surtido no es valido'),
            ('360', 'Datos Impuesto Especifico requerido La sección de datos impuesto especifico es requerido'),
            ('361', 'Cantidad Impuestos Mayor La cantidad de impuestos es mayor al permitido.'),
            ('362', 'Descuento por Regalia o Bonifificación Surtido Cuando al menos una línea del surtido tieene un descuento por regalía o bonficación se debe aplicar a todas las líneas'),
            ('363', 'Porcentaje Exoneracion No debe indicar % de exoneración cuando tiene surtidos con diferentes tarifas'),
            ('364', 'Monto Exoneracion El monto de exoneración no debe ser mayor al monto del impuesto'),
            ('365', 'Monto Total Requerido El monto total es requerido'),
            ('366', 'Identificación receptor no coincide con la del documento de referencia La identificación del receptor en el documento no coincide con la del documento original de la referencia'),
            ('367', 'Tipo documento referencia [Devolución Mercancia] solo aplica a Nota Crédito o Nota Débito Tipo documento referencia [Devolución Mercancia] solo aplica a Nota Crédito o Nota Débito'),
            ('370', 'Cantidad de referencias excede el permitido (10) Se ha superado el límite (10) de referencias permitidas para un documento.'),
            ('371', 'Tipo cambio diferente a la referencia El Tipo de cambio es diferente al tipo de cambio del documento de referencia'),
            ('372', 'Monto Ajustes supera documento referencia El monto del ajuste del documento supera el monto del documento referenciado'),
            ('373', 'Cabys no presente en documento de referencia  Uno de los cabys usado no se encuentra en el documento de referencia')
            ],
        required=True,
        tracking=True,
    )

    factura = fields.Many2one(
        string='Factura',
        required=False,
        comodel_name='account.move',
    )

    factura_NC = fields.Many2one(
        string='Factura NC',
        required=False,
        comodel_name='account.move',
    )

    factura_ND = fields.Many2one(
        string='Factura ND',
        required=False,
        comodel_name='account.move',
    )

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company
    )

    json = fields.Text(
        string="JSon",
        required=False,
        tracking=True,
    )

    def crear_factura(self):
        if self.codigo != '0':
            factura = self.crear_encabezado()
            # if self.factura.tipo_documento != '4':
            factura['Documentos'][0]['Encabezado']['Receptor'] = self.crear_receptor()
            factura['Documentos'][0]['Lineas'] = self.crear_lineas()
            factura['Documentos'][0]['Totales'] = self.crear_totales(factura['Documentos'][0]['Lineas'])
            factura['Documentos'][0]['Otros'] = {
                "Notas": text_from_html(self.factura.narration) if self.factura.narration else "Sin Notas"
            }

            self.enviar_documento(factura)

    def crear_nota_credito(self):
        if self.codigo != '0':
            factura = self.crear_encabezado()

            factura['Documentos'][0]['Encabezado']['Receptor'] = self.crear_receptor()

            factura['Documentos'][0]['Lineas'] = self.crear_lineas()

            factura['Documentos'][0]['Referencia'] = self.crear_referencia()

            factura['Documentos'][0]['Totales'] = self.crear_totales(factura['Documentos'][0]['Lineas'])

            factura['Documentos'][0]['Otros'] = {
                "Notas": "Factura de Referencia " + text_from_html(self.factura_NC.narration) if self.factura_NC.narration else "Sin Notas"
            }

            self.enviar_documento(factura)

    def enviar_documento(self, factura):
        self.json = factura
        company = self.factura.company_id
        url = company.gti_url + '/Documentos/CargarDocumento'
        # url = self.env.company.url_GTI
        params = {
            'pUsuario': company.gti_Usuario,
            'pClave': company.gti_Clave,
            'pNumCuenta': company.gti_NumCuenta,
        }

        header = {
            'Content-Type': 'application/json',
            'Accept': 'text/plain'
        }
        response = requests.post(url, headers=header, json=factura, verify=False, params=params)

        if response.status_code == 202:
            request = response.json()['Respuestas']
            if request[0]['Codigo'] == 0:
                self.consecutivo = str(request[0]['Consecutivo'])
                self.clave = str(request[0]['ClaveNumerica'])
                if self.tipo in ['1', '4']:
                    self.factura.clave_documento = str(request[0]['ClaveNumerica'])
                    self.factura.consecutivo = str(request[0]['Consecutivo'])
                elif self.tipo == '3':
                    self.factura_NC.clave_documento = str(request[0]['ClaveNumerica'])
                    self.factura_NC.consecutivo = str(request[0]['Consecutivo'])
                self.codigo = str(request[0]['Codigo'])
                self.consecutivo_Interno = str(request[0]['IdDocumento'])
            else:
                self.codigo = str(request[0]['Codigo'])
            msg = dict(self.fields_get(allfields=['codigo'])['codigo']['selection'])[self.codigo]
            if self.tipo in ['1', '4']:
                self.factura.message_post(body=_('Respuesta de GTI: %s - %s' % (self.codigo, msg)))
                _logger.info('Respuesta de GTI: %s - %s JSON: %s' % (self.codigo, msg, json.dumps(factura)))
            elif self.tipo == '3':
                self.factura_NC.message_post(body=_('Respuesta de GTI: %s - %s' % (self.codigo, msg)))
                _logger.info('Respuesta de GTI: %s - %s JSON: %s' % (self.codigo, msg, json.dumps(factura)))
        else:
            raise UserError(_('Error al enviar el documento: %s - %s') % (response.status_code, response.text))

    def crear_encabezado(self):
        user_tz = pytz.timezone(self.env.company.tz if self.env.company.tz else 'America/Costa_Rica')
        fechaActual = pytz.utc.localize(datetime.today()).astimezone(user_tz)

        self.fecha_Emsion = datetime.now()
        cajero = self.env['cajero'].sudo().search([('empleadoAsignado', '=', self.env.user.id)])
        if not cajero:
            raise UserError(_('El usuario que se encuentra realizado la acción no está asignado a ninguna caja'))

        factura = {
            "NumCuenta": int(self.env.company.gti_NumCuenta),
            "Documentos": [
                {
                    "Encabezado": {
                        # "FechaFactura": fechaActual.strftime("%Y-%m-%dT%H:%M:%S"),
                        "TipoDoc": int(self.tipo),
                        "SituacionEnvio": 1,
                        "CantDeci": 5,
                        "Sucursal": cajero.sucursal,
                        "CodigoActividad": self.factura.economic_activity_id.code,
                        "Terminal": int(cajero.terminal),
                        "Moneda": self.factura.currency_id.code if self.factura.currency_id.code else 1,
                        "CondicionVenta": "01",
                        "MedioPagos": [{
                            "TipoMedioPago": self.factura.payment_method if self.factura.payment_method else 4,
                        }],
                    }
                }
            ]
        }
        if self.factura.currency_id.name != 'CRC' and self.factura.invoice_currency_rate > 0:
            factura['Documentos'][0]['Encabezado']['TipoCambio'] = round(1 / self.factura.invoice_currency_rate, 5)
        if self.factura.tipoVenta == "2":
            factura['Documentos'][0]['Encabezado']['CondicionVenta'] = int(self.factura.tipoVenta)
            factura['Documentos'][0]['Encabezado']['PlazoCredito'] = int(self.factura.plazoVenta)
        else:
            factura['Documentos'][0]['Encabezado']['CondicionVenta'] = int(self.factura.tipoVenta)

        return factura

    def crear_receptor(self):
        # Ejemplo de como viene en el campo de Odoo +506 8912 2719, pero debe mandarse como  integer y sin código de país
        if self.factura.partner_id.phone:
            phone = phonenumbers.parse(self.factura.partner_id.phone, (self.factura.partner_id.country_id.code or "CR"))
            receptor = {
                "Nombre": self.factura.partner_id.name,
                "TipoIdent": int(self.factura.partner_id.tipo_Identificacion),
                "Identificacion": self.factura.partner_id.vat,
                "AreaTelefono": phone.country_code or 506,
                "NumTelefono": phone.national_number or 0,
            }
        else:
            receptor = {
                "Nombre": self.factura.partner_id.name,
                "TipoIdent": int(self.factura.partner_id.tipo_Identificacion),
                "Identificacion": self.factura.partner_id.vat,
            }
        if self.factura.partner_id.email:
            receptor['Correo'] = self.factura.partner_id.email
        if self.factura.partner_id.email_copy:
            receptor['Copia'] = self.factura.partner_id.email_copy
        if self.factura.receiver_economic_activity_id:
            receptor['ActividadEconomica'] = self.factura.receiver_economic_activity_id.code
        return receptor

    def crear_lineas(self):
        lineas = []
        for line in self.factura.invoice_line_ids.filtered(
        lambda x: x.display_type not in ('line_note', 'line_section') and x.product_id
        ):
            general = {
                "Cantidad": line.quantity,
                "CodigoComercial": [
                    {
                        "Tipo": "4",
                        "Codigo": str(line.product_id.default_code) if line.product_id.default_code else "000"
                    }
                ],
                "UnidadMedida": int(line.product_uom_id.code) if line.product_uom_id.code else 1,
                "Descripcion":  str(line.product_id.product_tmpl_id.display_name),
                "PrecioUnitario": round(line.price_unit,5),
                "CodProdServ": [line.product_id.product_tmpl_id.name],
                "Codigo": line.product_id.cabys if line.product_id.cabys else line.product_id.product_tmpl_id.cabys  ,

            }
            if line.discount > 0:
                subtotal_linea = line.price_unit * line.quantity
                monto_descuento = subtotal_linea * (line.discount / 100)
                general['Descuentos'] = [{
                    "MontoDescuento": round(monto_descuento, 5),
                    "CodigoDescuento": line.discount_code_id.code if line.discount_code_id else '07',
                    "DetalleDescuento": "Se aplica descuento.",
                }]
            if line.tax_ids:
                monto_impuesto = round(((line.price_unit * line.quantity) * (1 if line.discount >= 100 else (1 - (line.discount / 100.0)))) * (line.tax_ids.amount / 100.0), 5)
                general['Impuestos'] = [{
                    "CodigoImp": 1,
                    "PorcentajeImp": round(line.tax_ids.amount, 5),
                    "CodigoTarifa": int(line.tax_ids.codigo_Imp),
                    "MontoImp": monto_impuesto,
                    }]
                if line.discount_code_id.code in ("01", "03"):
                    general['ImpuestoAsumidoEmisorFabrica'] = monto_impuesto
            lineas.append(general)
        return lineas

    def crear_totales(self, lineas):
        service = ['5', '6', '7', '8', '9']
        # Filtrar líneas válidas
        lineas_validas = self.factura.invoice_line_ids.filtered(
            lambda x: x.display_type not in ('line_note', 'line_section') and x.product_id
        )
        # Pre-calcular TotalVentaNeta y TotalImpuesto para usarlos en TotalComprobante
        total_venta_neta = round(sum(
            line.price_subtotal
            for line in lineas_validas
        ), 5)
        total_impuesto = round(sum(
            ((line.price_unit * line.quantity) - (line.price_unit * line.quantity * (line.discount / 100))) * (line.tax_ids.amount / 100)
            for line in lineas_validas.filtered(lambda x: x.tax_ids)
        ), 5)
        totales = {
            "TotalServGravado": round(sum(
                line.price_unit * line.quantity
                for line in lineas_validas.filtered(
                    lambda x: x.product_id.cabys and str(x.product_id.cabys)[0] in service and x.tax_ids
                )
            ), 5),
            "TotalServExento": round(sum(
                line.price_unit * line.quantity
                for line in lineas_validas.filtered(
                    lambda x: x.product_id.cabys and str(x.product_id.cabys)[0] in service and not x.tax_ids
                )
            ), 5),
            "TotalServExonerado": 0.0,
            "TotalMercaGravada": round(sum(
                line.price_unit * line.quantity
                for line in lineas_validas.filtered(
                    lambda x: (not x.product_id.cabys or str(x.product_id.cabys)[0] not in service) and x.tax_ids
                )
            ), 5),
            "TotalMercaExenta": round(sum(
                line.price_unit * line.quantity
                for line in lineas_validas.filtered(
                    lambda x: (not x.product_id.cabys or str(x.product_id.cabys)[0] not in service) and not x.tax_ids
                )
            ), 5),
            "TotalMercaExonerada": 0.0,
            "TotalGravado": round(sum(
                line.price_unit * line.quantity
                for line in lineas_validas.filtered(lambda x: x.tax_ids)
            ), 5),
            "TotalExento": round(sum(
                line.price_unit * line.quantity
                for line in lineas_validas.filtered(lambda x: not x.tax_ids)
            ), 5),
            "TotalExonerado": 0.0,
            "TotalIVADevuelto": 0.0,
            "TotalOtrosCargos": 0.0,
            "TotalVenta": round(sum(
                line.price_unit * line.quantity
                for line in lineas_validas
            ), 5),
            "TotalDescuento": round(sum(
                (line.price_unit * line.quantity) * (line.discount / 100)
                for line in lineas_validas
            ), 5),
            "TotalVentaNeta": total_venta_neta,
            "TotalImpuesto": total_impuesto,
            "TotalComprobante": round(total_venta_neta + total_impuesto, 5),
        }
        total_impuesto_asumido_fabrica = 0.0
        for l in lineas:
            if l.get('ImpuestoAsumidoEmisorFabrica'):
                total_impuesto_asumido_fabrica += l['ImpuestoAsumidoEmisorFabrica']
        totales['TotalImpuestoAsumidoFabrica'] = round(total_impuesto_asumido_fabrica, 5)
        return totales

    def crear_referencia(self):
        user_tz = pytz.timezone(self.env.company.tz if self.env.company.tz else 'America/Costa_Rica')
        AccionRef = 0
        RazonNota = ""
        factura_NC = self.env['documento.hacienda'].sudo().search(['&',('factura','=',self.factura.id),('factura_NC','=',False),('factura_ND','=',False)])
        if factura_NC.factura.amount_total == self.factura.amount_total:
            AccionRef = 1
            RazonNota = "Se aplica nota de credito"
        else:
            AccionRef = 2
            RazonNota = "Se aplica nota de credito corrigiendo monto"

        fecha_Emsion = factura_NC.fecha_Emsion.astimezone(user_tz)

        referencia = {
            "TipoDocRef": int(factura_NC.tipo),
            "NumeroRef": factura_NC.consecutivo,
            "FechaRef": fecha_Emsion.strftime("%Y-%m-%dT%H:%M:%S"),
            "AccionRef": AccionRef,
            "RazonNota": RazonNota,
        }

        return referencia









