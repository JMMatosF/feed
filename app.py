api_request_delay = 2
import requests
import os
import xml.etree.ElementTree as ET
import csv
import subprocess
import json
import time
import os
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from bs4 import BeautifulSoup

# Função para obter informações da próxima página
def get_next_page_info(response):
    link_header = response.headers.get("Link")
    if link_header:
        next_page_match = re.search(r'<(.+)>;\s*rel="next"', link_header)
        if next_page_match:
            next_page_info = next_page_match.group(1)
            return next_page_info
    return None

def calculate_shipping_cost(weight, weight_unit, tags):
    # Convertendo o peso para float
    try:
        weight = float(weight)
    except ValueError:
        weight = 0  # Caso o peso não seja um número válido

    if weight_unit == 'g':
        weight /= 1000

    is_furniture = 'Mobiliário' in tags

    if is_furniture:
        # Tabela de preços para mobiliário
        if weight <= 3.99:
            return 6.85
        elif weight <= 29.99:
            return 13.10
        elif weight <= 54.99:
            return 19.35
        elif weight <= 79.99:
            return 25.60
        elif weight <= 300:
            return 78.10
        elif weight <= 500:
            return 119.35
        elif weight <= 800:
            return 263.10
        else:
            return 0 
    else:
        if weight <= 4.99:
            return 4.50
        elif weight <= 9.99:
            return 6.99
        elif weight <= 14.99:
            return 8.90
        elif weight <= 19.99:
            return 9.90
        elif weight <= 24.99:
            return 10.90
        elif weight <= 29.99:
            return 11.90
        elif weight <= 34.99:
            return 12.90
        elif weight <= 39.99:
            return 13.90
        elif weight <= 44.99:
            return 14.90
        elif weight <= 49.99:
            return 15.90
        elif weight <= 54.99:
            return 16.90
        elif weight <= 59.99:
            return 17.90
        elif weight <= 64.99:
            return 18.90
        elif weight <= 69.99:
            return 19.90
        elif weight <= 74.99:
            return 20.90
        elif weight <= 80:
            return 21.90
        elif weight <= 300:
            return 41.90
        elif weight <= 400:
            return 61.90
        else:
            return 0



# Função para buscar todos os produtos com uma tag específica
def fetch_all_products(shop_url, access_token, tag="KuantoKusta"):
    all_variants = []
    page_info = ""
    while True:
        url = f"https://{shop_url}/admin/api/2021-07/products.json?limit=250"
        if page_info:
            url += f"&page_info={page_info}"
        if tag:
            url += f"&tag={tag}"

        headers = {
            "X-Shopify-Access-Token": access_token
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            products_data = response.json().get('products', [])
            if not products_data:
                break

            for product in products_data:
                product_id = product['id']
                title = product['title']
                handle = product['handle']
                vendor = product['vendor']
                product_type = product['product_type']

                options = {option['position']: option['name'] for option in product.get('options', [])}

                for variant in product['variants']:
                    weight = variant.get('weight', '0')
                    weight_unit = variant.get('weight_unit', 'kg')
                    shipping_cost = calculate_shipping_cost(weight, weight_unit, tag)
                    variant_data = {
                        'Status': product.get('status', 'N/A'),
                        'Product ID': product_id,
                        'Title': title,
                        'Handle': handle,
                        'Variant SKU': variant['sku'],
                        'Variant Price': variant.get('price', 'N/A'),
                        'Variant Inventory Qty': variant.get('inventory_quantity', 'N/A'),
                        'Option1 Name': options.get(1, 'N/A'),
                        'Option1 Value': variant.get('option1', 'N/A'),
                        'Option2 Name': options.get(2, 'N/A'),
                        'Option2 Value': variant.get('option2', 'N/A'),
                        'Vendor': vendor,
                        'Product Type': product_type,
                        'Barcode': variant.get('barcode', 'N/A'),
                        'Weight': str(variant.get('weight', 'N/A')) + ' ' + variant.get('weight_unit', ''),
                        'Type': product.get('product_type','N/A'),
                        'Size':product.get('product_size','N/A'),
                        'Availability': variant.get('inventory_quantity', 'N/A'),
                        'Tags': product.get('tags','N/A'),
                        'Shipping_Cost': f"{shipping_cost} €",
                        'Min_delivery_time':product.get('min_delivery_time',1),
                        'Max_delivery_time':product.get('max_delivery_time',14),
                        'Image': product['images'][0]['src'] if product['images'] else "N/A",
                        'Description': product.get('body_html', 'N/A')
                    }
                    all_variants.append(variant_data)

            page_info = get_next_page_info(response)
            if not page_info:
                break
        elif response.status_code == 429:
            print("Rate limit exceeded. Waiting for a moment before retrying...")
            time.sleep(60)
        else:
            print(f"Error fetching products. Status code: {response.status_code}")
            break

    return all_variants

# Função para salvar os produtos buscados em um arquivo CSV
def fetch_all_products_to_csv(shop_url, access_token, tag, csv_filename):
    all_variants = fetch_all_products(shop_url, access_token, tag)

    if os.path.exists(csv_filename):
        print(f"O arquivo '{csv_filename}' já existe. Sobrescrevendo...")

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Status','Product ID', 'Title', 'Handle', 'Variant SKU', 'Variant Price', 'Variant Inventory Qty', 
                      'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value', 'Vendor', 'Product Type', 'Barcode','Image','Weight',
                        'Type','Size','Availability','Tags','Shipping_Cost','Min_delivery_time','Max_delivery_time','Description']
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        csv_writer.writeheader()

        for variant in all_variants:
            csv_writer.writerow(variant)

    print(f"Informações das variantes escritas com sucesso em '{csv_filename}'.")

# Função para gerar um arquivo XML a partir do arquivo CSV
def generate_xml_from_csv(csv_filename, xml_filename):
    root = Element('products')
    a = 0

    with open(csv_filename, mode='r', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            if str(row['Status']) == 'active':
                if int(row['Availability']) > 0:
                    product_element = SubElement(root, "product")
                    
                    if row['Barcode'] == "N/A":
                        continue
                    else :
                        SubElement(product_element, "upc_ean").text = row['Barcode'] if row['Barcode'] else "N/A"

                    SubElement(product_element, "reference").text = row['Variant SKU']
                    SubElement(product_element,"brand").text = row['Vendor']
                    SubElement(product_element, "category").text = row['Type']
                    designation = row['Title'] if row['Option1 Value'] == 'Default Title' else f"{row['Title']} {row['Option1 Value']}"
                    SubElement(product_element, "designation").text = designation                
                    regular_price = row['Variant Price'] + "€"
                    SubElement(product_element, "regular_price").text = regular_price
                    SubElement(product_element, "current_price").text = regular_price
                    SubElement(product_element, "availability").text = 'in stock'
                    SubElement(product_element, "stock").text = row['Variant Inventory Qty']
                    SubElement(product_element, "norma_shipping_cost").text = row['Shipping_Cost']
                    SubElement(product_element, "min_delivery_time").text = row['Min_delivery_time']
                    SubElement(product_element, "max_delivery_time").text = row['Max_delivery_time']
                    SubElement(product_element,"min_preparation_time").text = "1"
                    SubElement(product_element,"max_preparation_time").text = "14"
                    SubElement(product_element, "product_url").text = "https://abcescolar.pt/products/" + row['Handle']
                    #soup = BeautifulSoup(row['Description'], "html.parser")
                    #clean_description = soup.get_text(separator='\n')  # Usando '\n' como separador para preservar quebras de linha
                    #SubElement(product_element, "description").text = clean_description
                    SubElement(product_element, "description").text = row['Description']
                    SubElement(product_element, "image_url").text = row['Image']
                    SubElement(product_element, "size").text = row['Size'] 
                    SubElement(product_element, "weight").text = row['Weight']
                    SubElement(product_element,"quantiy").text = "1"
                    SubElement(product_element,"color").text = "N/A"
                    SubElement(product_element,"aux").text = "N/A"
                    
                    a = a +1
                else:
                    continue
            else:
                continue

    # Geração do XML e formatação
    xml_str = tostring(root, 'utf-8')
    reparsed = minidom.parseString(xml_str)
    pretty_xml_str = reparsed.toprettyxml(indent="  ")
    
    with open(xml_filename, "w", encoding='utf-8') as xmlfile:
        xmlfile.write(pretty_xml_str)

    print(f"XML file '{xml_filename}' generated successfully.")

def commit_and_push_to_github(repo_path, file_path, commit_message, token):
    # URL do repositório com o token de acesso pessoal
    repo_url = f'https://{token}@github.com/JMMatosF/feed.git'
    
    # Configurar o remote para usar o token
    subprocess.run(['git', '-C', repo_path, 'remote', 'set-url', 'origin', repo_url], check=True)
    
    # Adicionar todos os arquivos modificados ao stage
    subprocess.run(['git', '-C', repo_path, 'add', '.'], check=True)
    
    # Fazer commit
    subprocess.run(['git', '-C', repo_path, 'commit', '-m', commit_message], check=True)
    
    # Fazer push para o repositório remoto
    subprocess.run(['git', '-C', repo_path, 'push'], check=True)
    
    print(f"Arquivos comitados e enviados para o GitHub com sucesso.")

def criar_arquivo_na_shopify(api_key, loja, file_url):
    url = f"https://{loja}/admin/api/2024-04/graphql.json"
    
    headers = {
        "X-Shopify-Access-Token": api_key,
        "Content-Type": "application/json"
    }

    query = """
    mutation fileCreate($input: [FileCreateInput!]!) {
        fileCreate(files: $input) {
            files {
                ... on GenericFile {
                    id
                    url
                    alt
                }
            }
            userErrors {
                field
                message
            }
        }
    }
    """
    
    variables = {
        "input": [
            {
                "originalSource": file_url,
                "alt": "products_by_tag.json"
            }
        ]
    }

    response = requests.post(url, headers=headers, json={'query': query, 'variables': variables})
    
    if response.status_code == 200:
        response_data = response.json()
        if "errors" in response_data or "userErrors" in response_data.get('data', {}).get('fileCreate', {}):
            errors = response_data.get('errors') or response_data['data']['fileCreate']['userErrors']
            print(f"Erros na resposta GraphQL: {errors}")
        else:
            print("Arquivo JSON criado com sucesso na Shopify!")
            print("Resposta:", json.dumps(response_data, indent=4))
    else:
        print(f"Falha ao criar o arquivo JSON. Código de status: {response.status_code}")
        print("Resposta:", response.text)

if __name__ == "__main__":
    shop_url = "abc-escolar.myshopify.com"
    access_token = "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"
    api_key = "2c39bf093b7fd195f0484847a65a2648"
    password = "537bbbeae234e1a815a43d617e1aa8da"
    tag = "KuantoKusta"
    csv_filename = "products_by_tag.csv"
    xml_filename = "products_by_tag.xml"
    # fetch_all_products_to_csv(shop_url, access_token, tag, csv_filename)
    # generate_xml_from_csv(csv_filename, xml_filename)
    repo_path = r'C:\Users\jmato\PycharmProjects\feed'
    file_path = 'products_by_tag.json'
    commit_message = 'Atualização do arquivo JSON com novos dados'
    
    # Token de acesso pessoal do GitHub
    github_token = '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'
    
    # Commit e push para o GitHub
    commit_and_push_to_github(repo_path, file_path, commit_message, github_token)
    
    # URL bruta do arquivo JSON no GitHub
    github_raw_url = 'https://raw.githubusercontent.com/JMMatosF/feed/main/products_by_tag.json'
    
    # Criar um novo arquivo na Shopify
    criar_arquivo_na_shopify(access_token, shop_url, github_raw_url)