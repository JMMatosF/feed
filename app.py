import json
import time
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
import requests
import shopify
from bs4 import BeautifulSoup

api_request_delay = 2

ACCESS_TOKEN = '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'
API_VERSION = '2023-10'
API_KEY = '2c39bf093b7fd195f0484847a65a2648'
PASSWORD = '537bbbeae234e1a815a43d617e1aa8da'


def fetch_and_save_products_by_tag(shopify_store_url, tag, output_file, request_timeout=10):
    global response
    page = 1
    product_data = []

    while True:
        shopify.ShopifyResource.clear_session()
        shopify.ShopifyResource.site = shopify_store_url
        shopify.ShopifyResource.headers = {}

        # Construct the API endpoint with pagination and specify the API version
        api_endpoint = f"/admin/api/products.json?tags={tag}&limit=250&page={page}"

        # Make a GET request to the Shopify API with a timeout, using API key and password
        full_url = f"{shopify_store_url}{api_endpoint}"
        try:
            print(full_url)
            response = requests.get(full_url, auth=(API_KEY, PASSWORD))
        except requests.exceptions.Timeout:
            print("Request timed out. Retrying in a moment...")
            time.sleep(5)  # Sleep for 5 seconds and then retry
            continue

        # Check if the request was successful
        if response.status_code == 200:
            page_data = response.json().get('products')
            if not page_data:
                break  # No more pages to fetch
            product_data.extend(page_data)
            page += 1
        elif response.status_code == 401:
            print("Authentication failed. Please check your API key and password.")
            break
        else:
            print(f"Failed to retrieve product data. Status code: {response.status_code}")
            break

        # Introduce a delay to stay within rate limits
        time.sleep(api_request_delay)

    # Save all product data to the specified output file
    with open(output_file, 'w') as file:
        json.dump(product_data, file, indent=4)

    if response.status_code == 200:
        print(f"All products with the tag '{tag}' have been copied to '{output_file}'.")

def main():
    tag = "KuantoKusta"
    api_key = "532e586c6a52981c06caa7eeec38ee8c"
    access_token = "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"
    password = "79686ebe8e57a554f1c0d89ddf8503a5"
    output_file = 'products.json'
    shopify_store_url = 'https://abc-escolar.myshopify.com'  # Remove "https://"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    shopify.ShopifyResource.set_site("https://abcescolar.pt")
    products_url = f"https://abc-escolar.myshopify.com/admin/products.json"
    response = requests.get(products_url, auth=(api_key, password), headers=headers)
    fetch_and_save_products_by_tag(shopify_store_url, tag, output_file)
    page = 1
    per_page = 250

    # create the root element of the xml feed
    root = Element("products")

    # iterate through all products of vendor and paginate
    while True:
        products = shopify.Product.find(tags=tag, limit=per_page, page=page)

        for product in products:
            if tag in product.tags:
                for variant in product.variants:
                    product_element = SubElement(root, "product")
                    if variant.title == "Default Title":
                        SubElement(product_element, "designation").text = str(product.title)
                    else:
                        SubElement(product_element, "designation").text = str(product.title + " " + variant.title)
                    SubElement(product_element, "upc_ean").text = str(variant.sku)
                    SubElement(product_element, "reference").text = str(variant.sku)
                    # SubElement(product_element, "brand").text = str(product.vendor)
                    # SubElement(product_element, "category").text = str(product.product_type)
                    # SubElement(product_element, "category2").text = str(product.tags)
                    if product.variants[0].compare_at_price is None:
                        SubElement(product_element, "regular_price").text = str(variant.price) + "€"
                    else:
                        SubElement(product_element, "regular_price").text = str(
                            variant.compare_at_price) + "€"
                    SubElement(product_element, "current_price").text = str(variant.price) + "€"
                    # SubElement(product_element, "availability").text = "in stock"
                    # SubElement(product_element, "stock").text = "5"
                    # SubElement(product_element, "norma_shipping_cost").text = "5€"
                    # SubElement(product_element, "min_delivery_time").text = "1 dia"
                    # SubElement(product_element, "max_delivery_time").text = "5 dia"
                    # SubElement(product_element,
                    #          "product_url").text = "https://abcescolar.pt/products/" + product.handle
                    description = BeautifulSoup(product.body_html, "html.parser").get_text()
                    SubElement(product_element, "description").text = description
                    # ET.SubElement(product_element, "description").text = str(product.body_html)
                    # SubElement(product_element, "image_url").text = product.images[0].src
                    # SubElement(product_element, "size").text = "S"
                    # SubElement(product_element, "weight").text = str(product.variants[0].grams) + " g"
                    # SubElement(product_element, "quantity").text = "1"
                    # SubElement(product_element, "color").text = "variadas"
                    # SubElement(product_element, "aux").text = "variadas"

        # check if there are more products to paginate through
        if len(products) < per_page:
            break
        page += 1

    # create a pretty xml string
    xml_str = tostring(root, 'utf-8')
    reparsed = minidom.parseString(xml_str)
    pretty_xml_str = reparsed.toprettyxml(indent=" ", encoding='utf-8').decode('utf-8').replace('\0', '')

    # write the xml string to a file
    with open(f"{tag}.xml", "w", encoding="utf-8") as f:
        try:
            f.write(pretty_xml_str)
        except UnicodeEncodeError:
            f.write(pretty_xml_str.encode("ascii", "xmlcharrefreplace").decode())

    return xml_str


if __name__ == '__main__':
    main()
