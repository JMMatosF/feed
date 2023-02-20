import webbrowser
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
import requests
import shopify
from bs4 import BeautifulSoup
from flask import Flask, request

app = Flask(__name__)


@app.route('/index', methods=["GET", "POST"])
def generate_feed():
    # call the feed_generator function to generate the XML file
    tag = request.args.get("tag")
    main()
    # render the template and pass the generated xml file
    xml_feed = main()
    return xml_feed, 200, {'Content-Type': 'text/xml'}


def main():
    # Shopify API credentials
    tag = "KuantoKusta"
    # shop_url = "https://abc-escolar.myshopify.com"
    api_key = "532e586c6a52981c06caa7eeec38ee8c"
    access_token = "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"
    password = "79686ebe8e57a554f1c0d89ddf8503a5"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    shopify.ShopifyResource.set_site("https://abc-escolar.myshopify.com")
    products_url = f"https://abc-escolar.myshopify.com/admin/products.json"
    response = requests.get(products_url, auth=(api_key, password), headers=headers)
    # data = response.json()
    page = 1
    per_page = 250

    # create the root element of the xml feed
    root = Element("products")

    # iterate through all products of vendor and paginate
    while True:
        products = shopify.Product.find(tags=tag, limit=per_page, page=page)

        for product in products:
            if tag in product.tags:
                # create a new element for the product
                product_element = SubElement(root, "product")

                # add the title, sku, and vendor of the product as subelements
                SubElement(product_element, "upc_ean").text = str(product.variants[0].sku)
                SubElement(product_element, "reference").text = str(product.variants[0].sku)
                SubElement(product_element, "brand").text = str(product.vendor)
                SubElement(product_element, "category").text = str(product.product_type)
                SubElement(product_element, "designation").text = str(product.title)
                SubElement(product_element, "regular_price").text = product.variants[0].price + "€"
                SubElement(product_element, "current_price").text = ""
                SubElement(product_element, "availability").text = "in stock"
                SubElement(product_element, "stock").text = "5"
                SubElement(product_element, "norma_shipping_cost").text = "5.00€"
                SubElement(product_element, "min_delivery_time").text = "1 dia"
                SubElement(product_element, "max_delivery_time").text = "5 dia"
                SubElement(product_element, "product_url").text = "https://abcescolar.pt/products/" + product.handle
                description = BeautifulSoup(product.body_html, "html.parser").get_text()
                SubElement(product_element, "description").text = description

                # ET.SubElement(product_element, "description").text = str(product.body_html)
                SubElement(product_element, "image_url").text = product.images[0].src
                SubElement(product_element, "size").text = "S"
                SubElement(product_element, "weight").text = "1Kg"
                SubElement(product_element, "quantity").text = "1"
                SubElement(product_element, "color").text = "variadas"
                SubElement(product_element, "aux").text = "variadas"

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


main()

if __name__ == '__main__':
    app.run()
webbrowser.open("http:127.0.0.1:5000/index")
