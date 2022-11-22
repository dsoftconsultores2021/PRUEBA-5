# -*- encoding: utf-8 -*-

{
    'name': 'Tipo de Cambio Especial/Fecha Emisión',
    'summary': """
    	Tipo de Cambio Especial
    """,
    'version': '15.0.0.1',
    'category': 'Accounting',
    'description': """
       El usuario puede usar el Tipo de Cambio Especial para modificar este dato en:\n
       - Comprobantes de Cliente\n
       - Comprobantes de Proveedor
       - Pagos/Cobros
       - Asientos Contables en General
    """,
    'author': 'Franco Najarro-Dorniers Computer',
    'website': '',
    'depends': ['sale','account'],
    'data': [
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/account_payment_register_view.xml'
    ],
}
