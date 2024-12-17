from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException


def test_dark_without_logging():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(host)
        driver.find_element(By.ID, "theme-toggle").click()
        time.sleep(2)  # Considera usar WebDriverWait en lugar de sleep
        # 4. Verificar el fondo y color de elementos con clase 'card-dark'
        card_dark = driver.find_element(By.CLASS_NAME, "card-dark")
        bg_color = card_dark.value_of_css_property('background-color')
        color = card_dark.value_of_css_property('color')
        assert bg_color == 'rgba(28, 28, 30, 1)', f"El color de fondo de .card-dark no es el esperado: {bg_color}"
        assert color == 'rgba(255, 255, 255, 1)', f"El color del texto de .card-dark no es el esperado: {color}"

        # Navegación en la aplicación
        driver.find_element(By.LINK_TEXT, "Explore").click()
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "Team").click()
        time.sleep(2)
        driver.find_element(By.LINK_TEXT, "Explore UVLs").click()
        time.sleep(2)
        driver.find_element(By.ID, "clear-filters").click()
        driver.find_element(By.CSS_SELECTOR, ".hamburger").click()
        time.sleep(0.5)  # Espera
        driver.find_element(By.CSS_SELECTOR, ".sidebar-toggle").click()
        time.sleep(2)  # Espera a que se aplique el cambio de tema

        # Assertions para verificar los estilos en modo oscuro

        # # 1. Verificar el borde de elementos con clase 'error'
        # error_elements = driver.find_elements(By.CLASS_NAME, "error")
        # for elem in error_elements:
        #     border_color = elem.value_of_css_property('border-color')
        #     assert border_color == 'rgba(255, 77, 79, 1)', f"El color del borde de .error no es el esperado: {border_color}"

        # # 2. Verificar el fondo y color de elementos con clase 'alert-warning' en upload_dataset, por comprobar colores de los errores
        # alert_warning = driver.find_element(By.CLASS_NAME, "alert-warning")
        # bg_color = alert_warning.value_of_css_property('background-color')
        # color = alert_warning.value_of_css_property('color')
        # assert bg_color == 'rgba(90, 90, 0, 1)', f"El color de fondo de .alert-warning no es el esperado: {bg_color}"
        # assert color == 'rgba(255, 255, 255, 1)', f"El color del texto de .alert-warning no es el esperado: {color}"

        # # 3. Verificar el fondo y color de elementos con clase 'alert-success'
        # alert_success = driver.find_element(By.CLASS_NAME, "alert-success")
        # bg_color = alert_success.value_of_css_property('background-color')
        # color = alert_success.value_of_css_property('color')
        # assert bg_color == 'rgba(38, 77, 38, 1)', f"El color de fondo de .alert-success no es el esperado: {bg_color}"
        # assert color == 'rgba(212, 237, 217, 1)', f"El color del texto de .alert-success no es el esperado: {color}"
        # Open the login page
        driver.get(f"{host}/login")
        time.sleep(1)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)
        time.sleep(1)
        driver.get(f"{host}/dataset/upload")
        time.sleep(1)

        # 5. Verificar el estilo del Dropzone en modo oscuro
        dropzone = driver.find_element(By.ID, "myDropzone")
        border_color = dropzone.value_of_css_property('border-color')
        assert border_color == 'rgb(20, 122, 187)', f"El color del borde de #myDropzone no es el esperado: {border_color}"

        # 6. Verificar el texto del Dropzone
        dropzone_text = driver.find_element(By.ID, "dropzone-text")
        color = dropzone_text.value_of_css_property('color')
        assert color == 'rgba(221, 221, 221, 1)', f"El color del texto de #dropzone-text no es el esperado: {color}"

        # Puedes añadir más assertions siguiendo el mismo patrón para otros elementos clave

    except NoSuchElementException:
        raise AssertionError('Test failed! No such element found.')

    except ElementClickInterceptedException:
        raise AssertionError('Element click intercepted!')

    finally:
        close_driver(driver)
