from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
import json
import os
import time
from html import escape


with open("test_data.json", encoding="utf-8") as data_file:
    test_data = json.load(data_file)

os.makedirs("screenshots", exist_ok=True)
execution_steps = []


def capture_screenshot(driver, name):
    path = os.path.join("screenshots", f"{name}.png")
    driver.save_screenshot(path)
    return path


def handle_alert(driver):
    try:
        alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
        message = alert.text
        alert.accept()
        return message
    except TimeoutException:
        return "No alert"


def write_report(status, error_message=""):
    rows = "".join(
        f"<tr><td>{escape(step['name'])}</td><td>{escape(step['status'])}</td>"
        f"<td>{escape(step['details'])}</td></tr>"
        for step in execution_steps
    )
    report = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Selenium Execution Report</title>
<style>body{{font-family:Arial,sans-serif;margin:32px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left}}th{{background:#eee}}
.passed{{color:green}}.failed{{color:red}}</style></head><body>
<h1>Selenium Execution Report</h1>
<p><strong>Status:</strong> <span class="{status.lower()}">{escape(status)}</span></p>
<p><strong>Executed:</strong> {datetime.now().isoformat(timespec="seconds")}</p>
<p><strong>Error:</strong> {escape(error_message or "None")}</p>
<table><tr><th>Step</th><th>Status</th><th>Details</th></tr>{rows}</table>
</body></html>"""
    with open("execution_report.html", "w", encoding="utf-8") as report_file:
        report_file.write(report)

# Setup
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://automationexercise.com/")
driver.maximize_window()
wait = WebDriverWait(driver, 15)

wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Signup / Login")))

# Go to Signup/Login
driver.find_element(By.LINK_TEXT, "Signup / Login").click()
wait.until(EC.presence_of_element_located((By.NAME, "name")))

# Enter test data
driver.find_element(By.NAME, "name").send_keys(test_data["name"])
email = test_data["email"]
password = test_data["password"]

driver.find_element(By.XPATH, "//input[@data-qa='signup-email']").send_keys(email)

# Click Signup
signup_button = driver.find_element(By.XPATH, "//button[@data-qa='signup-button']")
driver.execute_script("arguments[0].click();", signup_button)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

# 🔥 CHECK: Email exists OR new signup
try:
    driver.find_element(By.XPATH, "//p[text()='Email Address already exist!']")
    print("Email exists → Login")
    execution_steps.append({"name": "Login", "status": "Passed", "details": "Existing email detected"})

    # LOGIN SECTION (IMPORTANT FIX)
    driver.find_element(By.XPATH, "//input[@data-qa='login-email']").send_keys(email)
    driver.find_element(By.XPATH, "//input[@data-qa='login-password']").send_keys(password)
    driver.find_element(By.XPATH, "//button[@data-qa='login-button']").click()
    handle_alert(driver)

    time.sleep(5)

except NoSuchElementException:
    print("New email → Creating account")
    execution_steps.append({"name": "Create account", "status": "Passed", "details": "New email used"})

    # Fill signup form
    driver.find_element(By.ID, "id_gender2").click()
    driver.find_element(By.ID, "password").send_keys(password)

    driver.find_element(By.ID, "days").send_keys(test_data["birth_day"])
    driver.find_element(By.ID, "months").send_keys(test_data["birth_month"])
    driver.find_element(By.ID, "years").send_keys(test_data["birth_year"])

    driver.find_element(By.ID, "first_name").send_keys(test_data["first_name"])
    driver.find_element(By.ID, "last_name").send_keys(test_data["last_name"])
    driver.find_element(By.ID, "address1").send_keys(test_data["address"])

    driver.find_element(By.ID, "country").send_keys(test_data["country"])
    driver.find_element(By.ID, "state").send_keys(test_data["state"])
    driver.find_element(By.ID, "city").send_keys(test_data["city"])
    driver.find_element(By.ID, "zipcode").send_keys(test_data["zipcode"])
    driver.find_element(By.ID, "mobile_number").send_keys(test_data["mobile_number"])

    create_account = driver.find_element(By.XPATH, "//button[contains(normalize-space(.), 'Create Account')]")
    driver.execute_script("arguments[0].click();", create_account)
    time.sleep(5)

    driver.find_element(By.XPATH, "//a[text()='Continue']").click()
    time.sleep(5)

# ✅ Ensure login success
try:
    driver.find_element(By.XPATH, "//a[contains(text(),'Logged in as')]")
    print("Login Successful")
    capture_screenshot(driver, "01-login-success")
    execution_steps.append({"name": "Login", "status": "Passed", "details": "User is logged in"})
except:
    print("Login Failed")
    input("Check error, press Enter to exit...")
    driver.quit()
    exit()

# Start with an empty cart so repeated test runs remain independent.
driver.get("https://automationexercise.com/view_cart")
wait.until(EC.url_contains("/view_cart"))
time.sleep(2)
while True:
    remove_buttons = driver.find_elements(By.CSS_SELECTOR, "a.cart_quantity_delete")
    if not remove_buttons:
        break
    driver.execute_script("arguments[0].click();", remove_buttons[0])
    wait.until(lambda current_driver: len(
        current_driver.find_elements(By.CSS_SELECTOR, "a.cart_quantity_delete")
    ) < len(remove_buttons))

# Go to Products
driver.get("https://automationexercise.com/products")
wait.until(EC.url_contains("/products"))
wait.until(EC.visibility_of_element_located((By.ID, "search_product")))

# Search product
driver.find_element(By.ID, "search_product").send_keys(test_data["product"])
search_button = driver.find_element(By.ID, "submit_search")
driver.execute_script("arguments[0].click();", search_button)
wait.until(EC.presence_of_element_located((By.XPATH, "(//a[text()='View Product'])[1]")))
capture_screenshot(driver, "02-product-search")
execution_steps.append({"name": "Search product", "status": "Passed", "details": test_data["product"]})

# Scroll (avoid ads)
driver.execute_script("window.scrollBy(0, 400);")

# Open first product (JS click)
product = driver.find_element(By.XPATH, "(//a[text()='View Product'])[1]")
driver.execute_script("arguments[0].click();", product)
wait.until(EC.visibility_of_element_located((By.ID, "quantity")))

# Add one product first. The cart page on this demo site has no editable
# quantity field, so the remaining quantity is added after the cart is opened.
qty = driver.find_element(By.ID, "quantity")
qty.clear()
qty.send_keys("1")

# Add to cart
add_to_cart = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(.), 'Add to cart')]"))
)
add_to_cart.click()
handle_alert(driver)
capture_screenshot(driver, "03-added-to-cart")
execution_steps.append({"name": "Add product to cart", "status": "Passed", "details": "Product added"})

# View cart
driver.get("https://automationexercise.com/view_cart")
wait.until(EC.url_contains("/view_cart"))
wait.until(EC.visibility_of_element_located((By.XPATH, "//td[@class='cart_description']/h4/a")))

# Update quantity after opening the cart. Automation Exercise increments the
# existing cart line when the same product is added again.
remaining_quantity = test_data["quantity"] - 1
if remaining_quantity > 0:
    driver.back()
    wait.until(EC.visibility_of_element_located((By.ID, "quantity")))
    qty = driver.find_element(By.ID, "quantity")
    qty.clear()
    qty.send_keys(str(remaining_quantity))
    add_to_cart = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(.), 'Add to cart')]"))
    )
    driver.execute_script("arguments[0].click();", add_to_cart)
    handle_alert(driver)
    driver.get("https://automationexercise.com/view_cart")
    wait.until(EC.url_contains("/view_cart"))
    wait.until(EC.visibility_of_element_located((By.XPATH, "//td[@class='cart_description']/h4/a")))

execution_steps.append({"name": "Update quantity", "status": "Passed", "details": str(test_data["quantity"])})

# 👉 Verify cart
product_name = driver.find_element(By.XPATH, "//td[@class='cart_description']/h4/a").text
quantity = driver.find_element(By.XPATH, "//td[@class='cart_quantity']/button").text

print("Product:", product_name)
print("Quantity:", quantity)
assert product_name, "Cart product name is empty"
assert quantity == str(test_data["quantity"]), f"Expected quantity {test_data['quantity']}, got {quantity}"
capture_screenshot(driver, "04-cart-verification")
execution_steps.append({"name": "Verify cart", "status": "Passed", "details": f"{product_name}, quantity {quantity}"})
print("Cart verification successful")
write_report("PASSED")
print("Execution report: execution_report.html")

driver.quit()