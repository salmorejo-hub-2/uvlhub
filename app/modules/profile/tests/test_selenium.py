# Generated by Selenium IDE

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver
from selenium.common.exceptions import NoSuchElementException


def test_check_user_uvl_models():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f'{host}/login')

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, 'email')
        password_field = driver.find_element(By.NAME, 'password')

        email_field.send_keys('user1@example.com')
        password_field.send_keys('1234')

        # Send the form
        password_field.send_keys(Keys.RETURN)

        # Wait a little while to ensure that the action has been completed
        time.sleep(4)

        driver.get(f'{host}/profile/summary')
        time.sleep(3)

        uvl_model = driver.find_element(
            By.XPATH, "/html/body/div/div/main/div/div[2]/div/div/div/table/tbody/tr[1]/td[3]/ul/li[1]/a")
        print(uvl_model.text)
        assert uvl_model.text == "Download", "No hay uvls en esta usuario"
    except NoSuchElementException:
        raise AssertionError('Test failed!')

    finally:

        # Close the browser
        close_driver(driver)
