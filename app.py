import requests
from flask import Flask, render_template, request, make_response, Response
from feed import main
import webbrowser
import shopify

app = Flask(__name__)


@app.route('/feed', methods=["GET", "POST"])
def generate_feed():
    # call the feed_generator function to generate the XML file
    tag = request.args.get("tag")
    main(tag="Clementoni")
    # render the template and pass the generated xml file
    xml_feed = main(tag)
    return xml_feed, 200, {'Content-Type': 'text/xml'}


if __name__ == '__main__':
    app.run()
webbrowser.open("http:127.0.0.1:5000/feed")
