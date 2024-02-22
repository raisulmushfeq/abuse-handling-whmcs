import requests
from flask import Flask, request, jsonify

app = Flask(__name__)


# WHMCS API URL
whmcs_api_url = "your_WHMCS_URL/includes/api.php"
# WHMCS API credentials
api_identifier = "your_WHMCS_API_Identifier"
api_secret = "your_WHMCS_API_Secret"


@app.route('/open_ticket', methods=['POST'])
def open_ticket():
    # Get data from POST request
    client_id = request.json['client_id']
    subject = request.json['subject']
    message = request.json['message']



    # Prepare the API data
    api_data = {
        "username": api_identifier,
        "password": api_secret,
        "action": "openticket",
        "deptid" : "6",  # Abuse Department
        "markdown": True,
        "admin": True,
        "priority": "High",
        "clientid": client_id,
        "subject": subject,
        "message": message
    }

    # Send the request to WHMCS API
    response = requests.post(whmcs_api_url, data=api_data)

    # Process and return the response
    return jsonify(response.text)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
