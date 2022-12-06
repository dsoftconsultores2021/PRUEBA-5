from odoo import models, fields
###########CONFIGURACION#################################################################################
##ORGANIZACION>>>>>>>>>>>>>>>>>
class organizacion(models.Model):
    _name = "iot.organizacion"
    _description = "Organizacion"

    org_nombre = fields.Char(string = "Nombre")
    org_codigo = fields.Char(string = "Codigo")
    sel_flota = fields.Selection(selection = [("Si","Si"),("No","No")], string = "Monitoreo de Flota", default = "Si", required = "True")
    sel_activos = fields.Selection(selection = [("Si","Si"),("No","No")], string = "Monitoreo de Activos", default = "Si", required = "True")
    sel_trabajadores = fields.Selection(selection = [("Si","Si"),("No","No")], string = "Monitoreo de Colaboradores", default = "Si", required = "True")
    

class grupo(models.Model):
    _name = "iot.grupo"
    _description = "Grupo"

    codigo = fields.Many2one("iot.organizacion", string = "Organizacion")
    nombre = fields.Char(string = "Nombre")
    codigo_grupo = fields.Char(string = "Codigo")

## DISPOSITIVOS#############################################################
class dispositivo(models.Model):
    _name="iot.dispositivo"
    _description="Lista de dispositivos registrados en el sistema"

class modelo(models.Model):
    _name="iot.dispositivo.modelo"
    _description="Lista de modelos de dispositivo"

    codigo_modelo = fields.Char(string = "Codigo")
    descripcion_modelo=fields.Char(string = "Descripcion")

class dato(models.Model):
    _name="iot.dispositivo.dato"
    _description="Datos por dispositivo"

    descripcion = fields.Char(string = "Descripcion")
    tipo_dato = fields.Float(string = "Tipo de dato")
    unidad_medidda = fields.Char(string = "Unidad de medida")
    valor_numerico = fields.Float(string = "Valor numerico")
    valor_min_num = fields.Float(string = "Valor minimo numerico")
    valor_max_num = fields.Float(string = "Valor maximo numerico")
    valor_entero = fields.Integer(string = "Valor entero")
    valor_min_entero = fields.Integer(string = "Valor minimo entero")
    valor_max_entero = fields.Integer(string = "Valor maximo entero")
    texto = fields.Char(string = "Texto")



#########################################################################
# 
class usuario(models.Model):
    _name = "iot.usuario"
    _description = "Usuarios"

    nombre_usuario = fields.Char(string ="USUARIO")
    contrasena = fields.Char(string ="CONTRASEÑA")

    user_id = fields.Char(string ="ID de USUARIO")
    name_user = fields.Char(string ="Nombres")
    last_name_user = fields.Char(string ="Apellidos")
    email = fields.Char(string ="Email institucional")
    pers_email = fields.Char(string ="Email personal")
    telf_perso = fields.Char(string ="Telefono personal")
    telf_casa =  fields.Char(string ="Telefono casa")
    movil = fields.Char(string ="Movil personal")
    otro_telf = fields.Char(string ="Otro telefono")
    #foto = fields.Binary(string="Foto del usuario")

    organizacion_id = fields.Many2one("iot.organizacion", string = "Organizacion")


class geocerca(models.Model):
    _name="iot.geocerca"
    _description = "Geocercas"

########>>>>>>>>>>FLOTA<<<<<<<<<<<<<<##########
class conductor(models.Model):
    _name="iot.conductor"
    _description="Conductores"

    conductor_nombre=fields.Char(string="Nombre")
    conductor_apellido=fields.Char(string="Apellido")
    conductor_vehiculo=fields.Char(string="Vehiculo asignado")
    conductor_mail=fields.Char(string="Correo")
    conductor_viaje_id=fields.Char(string="Id del viaje")

