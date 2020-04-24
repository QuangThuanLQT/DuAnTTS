{
    'name': 'web_product_search_suggestion',
    'category': 'Website',
    'author': 'VietERP/Vu',
    'summary': 'Website e-commerce search autocomplete with high-light match words and image',
    'version': '1.0',
    'description': "Website Search Suggestions",
    'depends': ['website_sale', 'tts_modifier_website'],
    'data': [
        'views/search.xml',
        'views/header.xml',
        'views/product_search_keyword.xml',
        'views/product_template.xml',
        'views/product_search_history.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.jpg'],
}
