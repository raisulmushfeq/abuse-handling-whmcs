from selenium import webdriver
import time
from bs4 import BeautifulSoup
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import re
import datetime
# For Web Requests
import requests
import json

# Setup some requirements
webnx_enabled = False

# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# Trying out Class for OOP

class Datacenter:
    def login_to_datacenter(self, user, user_elem, passwd, passwd_elem, twofactor, link, path=None, login_click=False):
        while True:
            if path is not None:
                driver.get(link + path)
            else:
                driver.get(link)
            user_field = driver.find_element(By.NAME, user_elem)
            password_field = driver.find_element(By.NAME, passwd_elem)
            user_field.send_keys(user)
            password_field.send_keys(passwd)
            # After automatically entering the login details, wait for the 2FA, if 2fa is enabled
            if login_click:
                driver.find_element(By.CLASS_NAME, 'login-button').click()
            if twofactor:
                login = input("Please login to " + link + " and press enter or 'restart'")
                if login == "restart":
                    continue  # starts the while loop again if restart is specified
                else:
                    break  # continues to script if restart is not specified
            else:  # if 2FA is not enabled or false, login to quadranet automatically with the login details
                time.sleep(1)
                driver.find_element(By.CLASS_NAME, 'btn-primary').click()


# needed information about quadranet
quadranet = Datacenter()
quadranet.username = 'your_username'  # Enter your quadranet username here
quadranet.username_element = 'username'  # HTML Name
quadranet.password = 'your_password'  # Enter your quadranet password here
quadranet.password_element = 'password'  # HTML Name
quadranet.twoFactor = True  # True or False
quadranet.url = 'https://neo.quadranet.com'  # Example 'neo.quadranet.com'
quadranet.login_path = "/login"

# needed information about datacenter
webNX = Datacenter()
webNX.username = 'your_username'  # Enter your Datacenter username here
webNX.username_element = 'login'  # HTML Name
webNX.password = 'your_password'  # Enter your Datacenter password here
webNX.password_element = 'pass'  # HTML Name
webNX.twoFactor = True  # True or False
webNX.url = 'https://clients.webnx.com'  # Example 'neo.quadranet.com'
webNX.login_path = None
webNX.click_login = True

# needed information about WHMCS
whmcs_username: str = 'your_username'  # Enter your WHMCS username here
whmcs_password = 'your_password'  # Enter your WHMCS password here
whmcs_2FA = True  # True or False
whmcs_url = 'your_WHMCS_URL'  # Example 'https://whmcs.domain.com/path_to_whmcs'

processed_ips = {}

driver = webdriver.Chrome()


# This function will send replies for suspended and already terminated users.
def send_suspended_reply(driver, url, is_processed, ip_address):
    # Go to the ticket again
    # Optional go to the link first
    # driver.get(url)
    # time.sleep(3)

    try:
        # Click on the reply button
        reply = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'follow_up'))
        )
        reply.click()

        # Write the reply message
        reply_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'reply_body'))
        )
        if is_processed == "suspended":
            reply_box.send_keys("Hello!" +
                                Keys.RETURN +
                                "Thank you for the notification. The user has been suspended for the activities mentioned." +
                                Keys.RETURN +
                                "Regards")
        elif is_processed == "old":
            reply_box.send_keys("Hello!" +
                                Keys.RETURN +
                                "Thank you for the notification. I can see that this was a old ticket and the user had been terminated at the time of the incident. There is nothing much to do about it anymore. We are always willing to co-operate on any abuse reports." +
                                Keys.RETURN +
                                "Regards")

        # Submit the reply
        service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
        submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')

        submit_button.click()

        print("Replied to Quadranet that " + ip_address + " is " + is_processed + " on " + url)

    except Exception as e:
        print("Error occurred while sending the reply:", str(e))


# Example usage:
# Assuming you have a webdriver instance named 'driver' already set up
# and 'url' contains the URL of the ticket
# send_ticket_reply(driver, url)


# Extract IP address from a line of text
def extract_ip(text_line):
    extracted_ip = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', text_line)
    if len(extracted_ip) > 0:
        ip_address_string = ''.join(extracted_ip)
        print("The abusive user IP is: " + ip_address_string)
        return ip_address_string
    else:
        print("Could not find IP Address")


# Function to open support ticket using WHMCS API run locally
# It is assumed that the API will open ticket on Abuse Department
def open_ticket(subject, body):
    ticket_api = "http://127.0.0.1:5000/open_ticket"
    payload = json.dumps({
        "client_id": userid,
        "subject": subject,
        "message": body
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", ticket_api, headers=headers, data=payload)
    print(response.text)
    # get the ticket ID
    response_parts = response.text.split(';')
    tid = None
    for part in response_parts:
        key, value = part.split('=')
        if key == 'id':
            whmcs_ticket_id = value
            break
    print(whmcs_url + "/supporttickets.php?action=view&id=" + whmcs_ticket_id)
    # Todo
    # Change the opened ticket status to Customer Reply Required, priority high

# Function to search for VPS on WHMCS
def search_vps_whmcs(ip_address):
    driver.get(whmcs_url + "/index.php")
    try:
        searchClick = driver.find_element(By.NAME, 'searchterm')
    except NoSuchElementException:
        # handle the case when there are no li_elements or there is no second li element
        print("Something went wrong on whmcs while trying to find manually entered IP")
        # Todo
        # Check to see if I am logged out of whmcs and log in again
        print("waiting for 5 minutes on " + str(datetime.datetime.now().strftime("%I:%M %p")) + " to " + str(
            (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%I:%M %p")))
        time.sleep(5 * 60)
        print("starting over!")
    searchClick.send_keys(ip_address)
    time.sleep(3)
    service_list = driver.find_element(By.CSS_SELECTOR, 'ul[data-type="service"]')
    # display what we are getting from the search result
    # print(service_list.text)
    # Find the anchor text for the service
    li_elements = service_list.find_elements(By.TAG_NAME, 'li')
    try:
        second_a_element = li_elements[1].find_element(By.CSS_SELECTOR, 'a')
        href_value = second_a_element.get_attribute('href')
        # Prints the WHMCS link that we will go to
        # print(href_value)
        # print("Proceeding to service of " + ip_address)
        # Now go to the client service
        driver.get(href_value)
        # Get the user ID
        match = re.search(r"userid=(\d+)", href_value)
        if match:
            userid = match.group(1)
            # print("User ID:", userid)
        else:
            print("User ID not found in URL")
    except IndexError:
        isterminated = input("can not find the user, is he terminated already? yes/no/suspended")
        # Todo
        # Shared hosting user hole notified korte hobe user ke, ticket theke shared hosting related data
        # extract korte hobe. Customer ke notified kora hoise sei option add korte hobe.

        if isterminated == "yes":
            processed_ips[ip_address] = "yes"
            # notify quadranet that user is already terminated
            print("Already terminated")







quadranet.login_to_datacenter(quadranet.username, quadranet.username_element, quadranet.password,
                              quadranet.password_element, quadranet.twoFactor, quadranet.url,
                              quadranet.login_path)
if webnx_enabled:
    webNX.login_to_datacenter(webNX.username, webNX.username_element, webNX.password, webNX.password_element,
                          webNX.twoFactor, webNX.url, webNX.login_path, webNX.click_login)
# Login to WHMCS
driver.get(whmcs_url + "/login.php")
username = driver.find_element(By.NAME, 'username')
password = driver.find_element(By.NAME, 'password')
username.send_keys(whmcs_username)
password.send_keys(whmcs_password)
time.sleep(3)
# Now login to the WHMCS - Press the button
# https://stackoverflow.com/questions/45527991/how-to-press-login-button-in-selenium-python-3
elem = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']")
elem.click()
# After automatically entering the login details, wait for the 2FA
if whmcs_2FA:
    input("Login using 2FA in WHMCS and press enter")
# loop through the tickets
while True:
    # Get the list of support tickets
    driver.get(quadranet.url + "/support")
    time.sleep(3)
    # Get the status of the first ticket in list
    try:
        ticketstatus = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ticket-status'))
        )
    except NoSuchElementException:
        # handle the case when there are no li_elements or there is no second li element
        print("Could not find any tickets on Quadranet")
        print("waiting for 5 minutes on " + str(datetime.datetime.now().strftime("%I:%M %p")) + " to " + str(
            (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%I:%M %p")))
        time.sleep(5 * 60)
        print("starting over!")
        continue
    # get the ticket ID of the first ticket in list
    ticketid = driver.find_element(By.CLASS_NAME, 'sorting_1')
    # Get the ticket ID to variable to work with. We are getting only the first text element
    ticket_id = ticketid.text.split()[0]
    # Set the URL to open the ticket
    url = f"{quadranet.url}/support/ticket/{ticket_id}"
    desiredStatus = "On Hold"
    if ticketstatus.text == "On Hold":
        # if the above condition is true, open the ticket
        driver.get(url)
        # get the text of header to get IP address from class no-margin (there is two class, I need the first class)
        try:
            headertext = driver.find_element(By.CLASS_NAME, 'no-margin')
        except NoSuchElementException:
            # Handle the NoSuchElementException when the element is not found
            print("Error: Element with class 'no-margin' not found. Skipping this ticket.")
            # Move to the next ticket (iteration of the while loop)
            continue
        # Prints the value we got from the header
        # print(headertext.text)
        # extract IP address from header if present
        # ip_address = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', headertext.text)[0]
        ip_address_list = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', headertext.text)
        if len(ip_address_list) > 0:
            ip_address = ip_address_list[0]
            # Reply right after detecting the ip if it is already in the suspended list
            if ip_address in processed_ips:
                # If the IP is already processed, get the termination status from the dictionary
                is_processed = processed_ips[ip_address]
                if is_processed == "suspended":
                    send_suspended_reply(driver, url, is_processed, ip_address)
                    continue
                elif is_processed == "old":
                    send_suspended_reply(driver, url, is_processed, ip_address)
                    continue
        else:
            # try to find IP address from the ticket:
            html_content = driver.page_source

            # Step 3: Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Step 4: Find the first line containing the desired text
            desired_text = "There has been a report of abuse on your server"
            lines = soup.find_all(string=True)
            # lines = soup.find_all(text=True)
            for line in lines:
                if desired_text in line:
                    text_line = line.strip()
                    extracted_ip = extract_ip(text_line)
            # handle the error, for example set ip_address to None or raise an exception
            # ip_address = input("Enter the IP address that you see on the report")
            # convert IP address as list type to string
            ip_address = ''.join(extracted_ip)

        # Get the date of when the ticket opened
        try:
            # Get the date of when the ticket opened
            quadranet_ticket_header = driver.find_element(By.CLASS_NAME, 'body-header').text
        except NoSuchElementException:
            # handle the case when there are no li_elements or there is no second li element
            print("Something went wrong on quadranet")
            print("waiting for 5 minutes on " + str(datetime.datetime.now().strftime("%I:%M %p")) + " to " + str(
                (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%I:%M %p")))
            time.sleep(5 * 60)
            print("starting over!")
            continue
        match = re.search(r'\d{2}/\d{2}/\d{4}', quadranet_ticket_header)  # we will get output as 12/19/2022
        raw_date = match.group(0)
        datetime_obj = datetime.datetime.strptime(raw_date, '%m/%d/%Y')
        quadranet_ticket_time = datetime_obj.strftime('%d/%m/%Y')  # we will get output as 19/12/2022

        # Also get abuse content
        abuse_body_element = driver.find_element(By.CLASS_NAME, 'body-content')
        abuse_body = abuse_body_element.get_attribute('innerHTML')

        # Remove HTML tags using regular expressions
        cleaned_report = re.sub(r'<.*?>', '', abuse_body)

        # Now, search for this IP in WHMCS

        driver.get(whmcs_url + "/index.php")
        try:
            searchClick = driver.find_element(By.NAME, 'searchterm')
        except NoSuchElementException:
            # handle the case when there are no li_elements or there is no second li element
            print("Something went wrong on whmcs while trying to find manually entered IP")
            # Todo
            # Check to see if I am logged out of whmcs and log in again
            print("waiting for 5 minutes on " + str(datetime.datetime.now().strftime("%I:%M %p")) + " to " + str(
                (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%I:%M %p")))
            time.sleep(5 * 60)
            print("starting over!")
            continue
        searchClick.send_keys(ip_address)
        time.sleep(3)
        service_list = driver.find_element(By.CSS_SELECTOR, 'ul[data-type="service"]')
        # display what we are getting from the search result
        # print(service_list.text)
        # Find the anchor text for the service
        li_elements = service_list.find_elements(By.TAG_NAME, 'li')
        try:
            second_a_element = li_elements[1].find_element(By.CSS_SELECTOR, 'a')
        except IndexError:
            # handle the case when there are no li_elements or there is no second li element
            if ip_address in processed_ips:
                # If the IP is already processed, get the termination status from the dictionary
                is_terminated = processed_ips[ip_address]
                if is_terminated == "yes":
                    print("Already terminated")
                    # notify quadranet about it
                    driver.get(url)
                    time.sleep(3)
                    # click on the reply button
                    reply = driver.find_element(By.ID, 'follow_up')
                    reply.click()
                    time.sleep(1)
                    reply = driver.find_element(By.ID, 'reply_body')
                    reply.send_keys("Hello!" +
                                    Keys.RETURN +
                                    "Thank you for the notification. The user has been already terminated for the report. As you know, we are always willing to co-operate on any abuse reports." +
                                    Keys.RETURN +
                                    "Regards")
                    service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
                    submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
                    submit_button.click()
                    print("Replied to Quadranet that the user has been notified. On " + url)
                    continue
            else:
                isterminated = input("can not find the user, is he terminated already? yes/no/suspended")
                if isterminated == "yes":
                    processed_ips[ip_address] = "yes"
                    # notify quadranet that user is already terminated
                    print("Already terminated")
                    # notify quadranet about it
                    driver.get(url)
                    time.sleep(3)
                    # click on the reply button
                    try:
                        reply = driver.find_element(By.ID, 'follow_up')
                    except NoSuchElementException:
                        # handle the case when there are no li_elements or there is no second li element
                        print("Something went wrong on quadranet")
                        print("waiting for 5 minutes on " + str(
                            datetime.datetime.now().strftime("%I:%M %p")) + " to " + str(
                            (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%I:%M %p")))
                        time.sleep(5 * 60)
                        print("starting over!")
                        continue
                    reply.click()
                    time.sleep(1)
                    reply = driver.find_element(By.ID, 'reply_body')
                    reply.send_keys("Hello!" +
                                    Keys.RETURN +
                                    "Thank you for the notification. The user has been already terminated for the report. As you know, we are always willing to co-operate on any abuse reports." +
                                    Keys.RETURN +
                                    "Regards")
                    service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
                    submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
                    submit_button.click()
                    print("Replied to Quadranet that the user has been terminated. On " + url)
                    continue
                elif isterminated == "suspended":
                    # send the ticket reply as the user is suspended
                    # go to the ticket again
                    driver.get(url)
                    time.sleep(3)
                    # click on the reply button
                    reply = driver.find_element(By.ID, 'follow_up')
                    reply.click()
                    time.sleep(1)
                    reply = driver.find_element(By.ID, 'reply_body')
                    reply.send_keys("Hello!" +
                                    Keys.RETURN +
                                    "Thank you for the notification. The user has been suspended for the activities mentioned." +
                                    Keys.RETURN +
                                    "Regards")
                    time.sleep(1)
                    service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
                    submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
                    submit_button.click()
                    print("Replied to Quadranet that the user is already suspended On " + url)
                    # Continue to next ticket (iteration of the while loop)
                    continue
                else:
                    print("Okay, take your time, pausing for now")
                    break
        href_value = second_a_element.get_attribute('href')
        # Prints the WHMCS link that we will go to
        # print(href_value)
        # print("Proceeding to service of " + ip_address)
        # Now go to the client service
        driver.get(href_value)
        # Get the user ID
        match = re.search(r"userid=(\d+)", href_value)
        if match:
            userid = match.group(1)
            # print("User ID:", userid)
        else:
            print("User ID not found in URL")
        time.sleep(3)
        # Find the select element by its name attribute
        try:
            select_element = driver.find_element(By.NAME, 'domainstatus')
        except NoSuchElementException:
            print("Something went wrong on whmcs while getting domain status")
            # Check if support pin is needed and then enable support pin access
            # todo
            print("waiting for 5 minutes on " + str(datetime.datetime.now().strftime("%I:%M %p")) + " to " + str(
                (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%I:%M %p")))
            time.sleep(5 * 60)
            print("starting over!")
            continue
        # Create a Select object to interact with the select element
        select = Select(select_element)

        # Get the selected option element
        selected_option = select.first_selected_option

        # Get the value of the selected option
        selected_status = selected_option.get_attribute('value')

        # Get the hostname of the service
        hostname = driver.find_element(By.NAME, 'domain').get_attribute("value")
        # Get Registration date for the product
        registration_date = driver.find_element(By.NAME, 'regdate').get_attribute("value")
        registration_date_obj = datetime.datetime.strptime(registration_date, '%d/%m/%Y').date()
        # print(hostname)
        print(
            "The user is currently " + selected_status + ". Service registered on " + registration_date + " and the quadranet ticket opened on " + quadranet_ticket_time)  # This will print the selected status, in this case "Suspended"
        # calculate the difference between the dates
        date_diff = datetime_obj.date() - registration_date_obj
        # get the absolute difference between the dates
        days_diff = abs(date_diff.days)
        # check if the difference is positive or negative
        if date_diff.days > 0:
            print(f"The quadranet ticket was created {days_diff} days after the registration date.")
        elif date_diff.days < 0:
            print(f"The quadranet ticket was created {days_diff} days before the registration date.")
            # This will be executed if I see that the report is old and abusive user is terminated already
            # Store that the ticket is old for further processing:
            processed_ips[ip_address] = "old"
            # notify quadranet about it
            driver.get(url)
            time.sleep(3)
            # click on the reply button
            reply = driver.find_element(By.ID, 'follow_up')
            reply.click()
            time.sleep(1)
            reply = driver.find_element(By.ID, 'reply_body')
            reply.send_keys("Hello!" +
                            Keys.RETURN +
                            "Thank you for the notification. I can see that this was a old ticket and the user had been terminated at the time of the incident. There is nothing much to do about it anymore. We are always willing to co-operate on any abuse reports." +
                            Keys.RETURN +
                            "Regards")
            time.sleep(1)
            service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
            submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
            submit_button.click()
            print("Replied to Quadranet that the ticket is old. On " + url)
            continue
        else:
            print("The quadranet ticket was created on the same day as the registration date.")

        if selected_status == "Suspended":
            processed_ips[ip_address] = "suspended"
            # send the ticket reply as the user is suspended
            # go to the ticket again
            driver.get(url)
            time.sleep(3)
            # click on the reply button
            reply = driver.find_element(By.ID, 'follow_up')
            reply.click()
            time.sleep(1)
            reply = driver.find_element(By.ID, 'reply_body')
            reply.send_keys("Hello!" +
                            Keys.RETURN +
                            "Thank you for the notification. The user has been suspended for the activities mentioned." +
                            Keys.RETURN +
                            "Regards")
            time.sleep(1)
            service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
            submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
            submit_button.click()
            print("Replied to Quadranet that the user is already suspended On " + url)
            # Continue to next ticket (iteration of the while loop)
            continue
        elif selected_status == "Active":
            print("Initializing Active User Procedure on Abuse Ticket..." + url)
            time.sleep(3)
            ticketsList = driver.find_element(By.ID, 'clientTab-11')
            # print(ticketsList.get_attribute('href'))
            # Go to the ticket URL
            driver.get(ticketsList.get_attribute('href'))
            # should we open the ticket?
            user_input = input(
                "Press t to open ticket, n to let them know user notified already, or 'suspend', 'old', any other key to exit")
            if user_input == "t":
                print("#####################################")
                print("This information may help you..")
                print("Service IP: " + ip_address)
                print("Reference " + ticket_id)
                print("Service Hostname: " + hostname)
                print("#####################################")
                # Creating the customer abuse ticket from WHMCS

                # Construct ticket subject
                ticket_subject = "Report of abuse from server " + ip_address + \
                                 " (ref: " + ticket_id + " ) - Immediate action required"
                # Construct Ticket Body
                ticket_body = ("There has been a report of abuse on your server (" + ip_address + ") \n" +
                               "Per our policies, we require that all our clients respond to abuse notices as they "
                               "come in. Failure to do so within a timely manner (within 24 hours) will result in a "
                               "suspension of services until the server administrator has time to resolve the issue. \n"
                               +
                               "The initial complaint is attached to this ticket. If you don't see it under my "
                               "signature, please log in to your billing interface and view the ticket there. \n" +
                               "We will await your response indicating that you have complied with the order, "
                               "dispute it, or require a reasonable extension of time to resolve the issue. \n"
                               "Awaiting your timely response, \n"
                               "Raisul \n"
                               "IT Nut Hosting \n"
                               "```\n"
                               + cleaned_report + "\n"
                               "```")

                # Open the abuse ticket
                open_ticket(ticket_subject, ticket_body)

                print("getting back to the original abuse report to let them know that user is notified")

                driver.get(url)
                time.sleep(3)
                # click on the reply button
                reply = driver.find_element(By.ID, 'follow_up')
                reply.click()
                time.sleep(1)
                reply = driver.find_element(By.ID, 'reply_body')
                reply.send_keys("Hello!" +
                                Keys.RETURN +
                                "Thank you for the notification. The user has been notified about this matter. As per our company policy, we allow 24 hours for our customers to respond to a support ticket. If no response is provided, we will suspend their service if required." +
                                Keys.RETURN +
                                "Regards")
                time.sleep(1)
                service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
                submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
                submit_button.click()
                print("Replied to Quadranet that the user has been notified. On " + url)
            elif user_input == "n":
                driver.get(url)
                time.sleep(3)
                # click on the reply button
                reply = driver.find_element(By.ID, 'follow_up')
                reply.click()
                time.sleep(1)
                reply = driver.find_element(By.ID, 'reply_body')
                reply.send_keys("Hello!" +
                                Keys.RETURN +
                                "Thank you for the notification. The user has been notified about this matter. As per our company policy, we allow 24 hours for our customers to respond to a support ticket. If no response is provided, we will suspend their service if required." +
                                Keys.RETURN +
                                "Regards")
                service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
                submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
                submit_button.click()
                print("Replied to Quadranet that the user has been notified. On " + url)
            elif user_input == "suspend":
                # go to the product page
                driver.get(href_value)
                # suspend
                print("Suspending the service")
                driver.find_element(By.ID, "btnSuspend").click()
                time.sleep(3)
                # enter the reason for suspend
                reasonbox = driver.find_element(By.ID, "suspreason")
                reasonbox.send_keys('Multiple Frequent Abuse reports')
                # enable checkbox to send mail
                driver.find_element(By.ID, "suspemail").click()
                # finally press the suspend button
                driver.find_element(By.ID, 'ModuleSuspend-Yes').click()
                time.sleep(5)
                # notify quadranet about it
                driver.get(url)
                time.sleep(3)
                # click on the reply button
                reply = driver.find_element(By.ID, 'follow_up')
                reply.click()
                time.sleep(1)
                reply = driver.find_element(By.ID, 'reply_body')
                reply.send_keys("Hello!" +
                                Keys.RETURN +
                                "Thank you for the notification. The user has now been suspended for multiple abuse reports. We are always willing to co-operate on any abuse reports." +
                                Keys.RETURN +
                                "Regards")
                service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
                submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
                submit_button.click()
                print("Replied to Quadranet that the user has been suspended. On " + url)
                continue
            elif user_input == "old":
                # This will be executed if I see that the report is old and abusive user is terminated already
                # notify quadranet about it
                driver.get(url)
                time.sleep(3)
                # click on the reply button
                reply = driver.find_element(By.ID, 'follow_up')
                reply.click()
                time.sleep(1)
                reply = driver.find_element(By.ID, 'reply_body')
                reply.send_keys("Hello!" +
                                Keys.RETURN +
                                "Thank you for the notification. I can see that this was a old ticket and the user had been terminated at the time of the incedent. There is nothing much to do about it anymore. We are always willing to co-operate on any abuse reports." +
                                Keys.RETURN +
                                "Regards")
                service_list = driver.find_element(By.CLASS_NAME, 'modal-footer')
                submit_button = service_list.find_element(By.CLASS_NAME, 'btn-primary')
                submit_button.click()
                print("Replied to Quadranet that the ticket is old. On " + url)
                continue
            elif user_input != "":
                break
    # else:  # if the first listed ticket on Quadranet is not "On Hold" meaning open ticket actually
    #     print("No On Hold tickets found")
    #     print("waiting for 5 minutes on " + str(datetime.datetime.now().strftime("%I:%M %p")) + " to " + str(
    #         (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%I:%M %p")))
    #     time.sleep(5 * 60)
    #     print("starting over!")

    print("No Quadranet Ticket found, moving on to WebNX")

    if webnx_enabled:
        # Process WebNX Abuse Ticket
        # Go to support ticket page
        driver.get(webNX.url + "/client/ticket_list.php?type_select=My")
        html_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'list_container'))
        )
        # Get List Of tickets
        # Get the inner HTML content from the WebElement
        html_content = html_element.get_attribute("innerHTML")
        # Create a BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all ticket rows
        ticket_rows = soup.select('tr.odd, tr.even')

        # Define the filter criteria
        desired_department = "Abuse"
        desired_updated = "none"

        # Initialize a variable to store the ticket ID
        desired_ticket_id = None

        # Loop through each ticket row
        for row in ticket_rows:
            # Extract ticket details
            department = row.select_one('td:nth-child(8)').text
            updated = row.select_one('td:nth-child(5)').text

            # Check if the ticket matches the filter criteria
            if department == desired_department and updated == desired_updated:
                # Extract and store the ticket ID
                ticket_id = row.select_one('td:nth-child(1) a').text
                desired_ticket_id = ticket_id
                break  # Stop iterating since we found the desired ticket

        # Print the extracted ticket ID
        if desired_ticket_id:  # If a ticket is found that is needed action
            print("Desired Ticket ID:", desired_ticket_id)
            # Open the ticket on browser
            driver.get(webNX.url + "/client/ticket_view.php?ticket=" + desired_ticket_id)
            # Get IP address from subject
            html_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'check_ticket'))
            )
            # Get List Of tickets
            # Get the inner HTML content from the WebElement
            html_content = html_element.get_attribute("innerHTML")
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.find('h1').get_text(strip=True)
            print(text)
            # Get IP Address from ticket Subject
            extracted_ip = extract_ip(text)
            # Search on WHMCS with the IP
            search_vps_whmcs(extracted_ip)
        else:
            print("No ticket found matching the criteria.")

    # Wait and then start over
    print("No On Hold tickets found")
    print("waiting for 5 minutes on " + str(datetime.datetime.now().strftime("%I:%M %p")) + " to " + str(
        (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%I:%M %p")))
    time.sleep(5 * 60)
    print("starting over!")

print("exiting...")
driver.quit()
