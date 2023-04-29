from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import re
import datetime

# needed information about quadranet
quadranet_username: str = 'your_username'      # Enter your quadranet username here
quadranet_password = 'your_password'      # Enter your quadranet password here
quadranet_2FA = True                        # True or False
quadranet_url = 'https://neo.quadranet.com'     # Example 'neo.quadranet.com'

# needed information about WHMCS
whmcs_username: str = 'your_username'        # Enter your WHMCS username here
whmcs_password = 'your_password'             # Enter your WHMCS password here
whmcs_2FA = True                            # True or False
whmcs_url = 'your_WHMCS_URL'     # Example 'https://whmcs.domain.com/path_to_whmcs'

driver = webdriver.Chrome()
while True:
    driver.get(quadranet_url + "/login")
    username = driver.find_element(By.NAME, 'username')
    password = driver.find_element(By.NAME, 'password')
    username.send_keys(quadranet_username)
    password.send_keys(quadranet_password)
    # After automatically entering the login details, wait for the 2FA, if 2fa is enabled
    if quadranet_2FA:
        login = input("Please login to Quadranet and press enter or 'restart'")
        if login == "restart":
            continue  # starts the while loop again if restart is specified
        else:
            break  # continues to to script if restart is not specified
    else:   # if 2FA is not enabled or false, login to quadranet automatically with the login details
        time.sleep(1)
        driver.find_element(By.CLASS_NAME, 'btn-primary').click()
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
    driver.get(quadranet_url + "/support")
    time.sleep(3)
    # Get the status of the first ticket in list
    ticketstatus = driver.find_element(By.CLASS_NAME, 'ticket-status')
    # get the ticket ID of the first ticket in list
    ticketid = driver.find_element(By.CLASS_NAME, 'sorting_1')
    # Get the ticket ID to variable to work with. We are getting only the first text element
    ticket_id = ticketid.text.split()[0]
    # Set the URL to open the ticket
    url = f"{quadranet_url}/support/ticket/{ticket_id}"
    desiredStatus = "On Hold"
    if ticketstatus.text == "On Hold":
        # if the above condition is true, open the ticket
        driver.get(url)
        # get the text of header to get IP address from class no-margin (there is two class, I need the first class)
        headertext = driver.find_element(By.CLASS_NAME, 'no-margin')
        # Prints the value we got from the header
        # print(headertext.text)
        # extract IP address from header if present
        #ip_address = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', headertext.text)[0]
        ip_address_list = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', headertext.text)
        if len(ip_address_list) > 0:
            ip_address = ip_address_list[0]
        else:
            # handle the error, for example set ip_address to None or raise an exception
            ip_address = input("Enter the IP address that you see on the report")
        print("The abusive user IP is: " + ip_address)
        # Now, search for this IP in WHMCS
        driver.get(whmcs_url + "/index.php")
        searchClick = driver.find_element(By.NAME, 'searchterm')
        searchClick.send_keys(ip_address)
        time.sleep(3)
        service_list = driver.find_element(By.CSS_SELECTOR, 'ul[data-type="service"]')
        # display what we are getting from the search result
        # print(service_list.text)
        # Find the ancor text for the service
        li_elements = service_list.find_elements(By.TAG_NAME, 'li')
        try:
            second_a_element = li_elements[1].find_element(By.CSS_SELECTOR, 'a')
        except IndexError:
            # handle the case when there are no li_elements or there is no second li element
            isterminated = input("can not find the user, is he terminated already? yes/no")
            if isterminated == "yes":
                # notify quadranet that user is already terminated
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
                print("Okay, take your time, pausing for now")
                break
        href_value = second_a_element.get_attribute('href')
        # Prints the WHMCS link that we will go to
        #print(href_value)
        print("Proceeding to service of " + ip_address)
        # Now go to the client service
        driver.get(href_value)
        # Get the user ID
        match = re.search(r"userid=(\d+)", href_value)
        if match:
            userid = match.group(1)
            print("User ID:", userid)
        else:
            print("User ID not found in URL")
        # Find the select element by its name attribute
        select_element = driver.find_element(By.NAME, 'domainstatus')

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
        # print(hostname)
        print("The user is currently " + selected_status + " Service registered on " + registration_date)  # This will print the selected status, in this case "Suspended"

        if selected_status == "Suspended":
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
                            "Thank you for the notification. The user has been suspended for the activities mentioned."+
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
            #print(ticketsList.get_attribute('href'))
            # Go to the ticket URL
            driver.get(ticketsList.get_attribute('href'))
            #should we open the ticket?
            user_input = input("Press Enter to continue to next ticket, or any other key to exit, t to see ticket content, n to let them know user notified already, or 'suspend', 'old'")
            if user_input == "t":
                driver.get(url)
                print("#####################################")
                print("This information may help you..")
                print("Service IP: " + ip_address)
                print("Reference " + ticket_id)
                print("Service Hostname: " + hostname)
                print("#####################################")
                print("You will need to copy in the following order 1. IP Address, 2. Reference 3. Abuse Report")
                user_input = input("press enter again once you have copied the report, q, restart")
                if user_input == "q":
                    break
                elif user_input == "restart":
                    continue
                # Creating the customer abuse ticket from WHMCS
                print("getting back to the original abuse report to let them know that user is notified")
                # Get back to ticket on whmcs
                driver.get(whmcs_url + "/supporttickets.php?action=open&userid=" + userid)
                # Implementing the while loop to prevent accidental enters
                while True:
                    proceed = input("type 'submit' after entering the abuse report to submit the report")
                    if proceed == "submit":
                        break
                driver.find_element(By.ID, 'btnOpenTicket').click()
                time.sleep(3)
                ticket_status_select = driver.find_element(By.ID, 'ticketstatus')
                ticket_status = Select(ticket_status_select)
                ticket_status.select_by_value("Customer Reply Req.")
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
                print("Replied to Quadranet that the user has been notified. On " + url)
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
            elif user_input != "":
                break
    else:
        print("No On Hold tickets found")
        print("waiting for 30 minutes on " + str(datetime.datetime.now().strftime("%I:%M %p")) + " to " + str((datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime("%I:%M %p")))
        time.sleep(30*60)
        print("starting over!")
        continue
    user_input = input("Press Enter to continue to next ticket, or any other key to exit: ")
    if user_input == "":
        continue  # continue to the next iteration of the loop
        # if any other key was pressed, break out of the loop
    break
print("exiting...")
driver.quit()
