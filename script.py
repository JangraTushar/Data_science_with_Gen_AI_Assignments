import os
import time
import urllib.request

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException, NoSuchWindowException
from selenium.webdriver.common.action_chains import ActionChains


driver = webdriver.Edge()

wait = WebDriverWait(driver, 15)

driver.get("https://www.coned.com/en")
    
# Optional: Maximize the window
driver.maximize_window()

# Stay on the page for 5 seconds to look at it
time.sleep(2)

login_nav_btn = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//button[contains(@class, 'js-nav-login') and .//span[contains(text(), 'Log In or Register')]]")
))
login_nav_btn.click()
print("Clicked the 'Log In or Register' dropdown button.")


email_field = wait.until(EC.visibility_of_element_located((By.ID, "modal-login-email")))
email_field.clear()
email_field.send_keys("Payables2@dolphinps.com")


password_field = driver.find_element(By.ID, "modal-login-password")
password_field.clear()
password_field.send_keys("Ruper@2022")

password_field.send_keys(Keys.RETURN)
print("Submitted initial login form. Waiting for MFA/Security code screen...")

# 6. Wait for Multi-Factor Authentication (MFA) screen and locate the Security Code box
# XPath equivalent: "//input[@id='form-login-mfa-code']"
mfa_field = wait.until(EC.visibility_of_element_located((By.ID, "form-login-mfa-code")))
mfa_field.clear()

# Prompt you to type the security code into your console/terminal since it changes every time
#security_code = input("Please enter the MFA security code sent to your phone/email: ")
mfa_field.send_keys("Ruper")

# 7. Press Enter to submit the security code and complete the login process
mfa_field.send_keys(Keys.RETURN)
print("Security code submitted successfully.")


SAVE_DIR = r"E:\Basic_automation\downloaded_bills"   # replace with your folder path
os.makedirs(SAVE_DIR, exist_ok=True)

account_numbers = [26058352977,59496094778, 13596927304, 27683399326, 58210728901, 63920734165, 21589248190, 33259446764]

for account_number in account_numbers:
    acc_no = str(account_number)

    try:
        print(f"Attempting to process account: {acc_no}")

        # 1. Locate the parent menu button
        button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[@id='account_info']/button")
        ))

        # Scroll it into view smoothly
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
        time.sleep(0.5)

        # 2. Click the dropdown button to lock the menu open instead of just hovering
        ActionChains(driver).move_to_element(button).click().perform()
        print("Opened the account section dropdown.")


        search_box_xpath = "//input[contains(@class, 'js-text-search-input')]"

        # 2. Click the dropdown button only if the search box is not already visible
        already_open = [e for e in driver.find_elements(By.XPATH, search_box_xpath) if e.is_displayed()]
        if not already_open:
            ActionChains(driver).move_to_element(button).click().perform()
        print("Opened the account section dropdown.")

        # 3. Pick the search box that is actually displayed (skips hidden mobile copies)
        search_box = wait.until(lambda d: next(
            (e for e in d.find_elements(By.XPATH, search_box_xpath) if e.is_displayed()), False))
        print("Matching inputs in DOM:", len(driver.find_elements(By.XPATH, search_box_xpath)))

        # 4. Click the search box
        ActionChains(driver).move_to_element(search_box).click().perform()
        driver.execute_script("arguments[0].focus();", search_box)
        print("Clicked the center of the search box.")

        # 5. Wait for 2 seconds exactly as requested after the click
        time.sleep(2)

        # 6. Enter the account number, also set the attribute so it shows in the DOM
        driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].setAttribute('value', arguments[1]);
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: '0' }));
            """,
            search_box, acc_no
        )
        print(f"Successfully entered value: {acc_no}")


                # 7. Wait for the dropdown list to filter (up to ~10 seconds)
        # Match on the highlighted account number, because before filtering the list
        # shows ALL accounts and the first item would be the wrong one
        item_xpath = (f"//li[contains(@class,'js-account-dropdown-search-item-desktop')]"
                      f"[.//span[contains(@class,'highlight-text')][contains(.,'{acc_no}')]]")
        nomatch_xpath = "//strong[contains(text(),'No Matching Results')]"

        found_items = []
        no_match = False
        for attempt in range(10):
            time.sleep(1)
            found_items = [e for e in driver.find_elements(By.XPATH, item_xpath) if e.is_displayed()]
            no_match = any(e.is_displayed() for e in driver.find_elements(By.XPATH, nomatch_xpath))
            if found_items or no_match:
                break

        # 8a. No account for this number -> skip to the next number
        if not found_items:
            print(f"No account found for {acc_no} - skipping")
            # close the dropdown so the next iteration can open it again
            ActionChains(driver).move_to_element(button).click().perform()
            time.sleep(1)
            continue

        # 8b. Account found -> click the first item in the list
        # first_item = found_items[0]
        # address = first_item.find_element(
        #     By.XPATH, ".//p[contains(@class,'account-dropdown-logged-in__address')]").text.strip()
        # print(f"Account found: {address}")
        # driver.execute_script("arguments[0].click();", first_item)


        first_item = found_items[0]
        address = first_item.find_element(
            By.XPATH, ".//p[contains(@class,'account-dropdown-logged-in__address')]").text.strip()
        print(f"Account found: {address}")

        # real mouse click (the site may ignore a JavaScript click)
        driver.execute_script("arguments[0].scrollIntoView({block:'nearest'});", first_item)
        try:
            ActionChains(driver).move_to_element(first_item).click().perform()
        except Exception:
            driver.execute_script("arguments[0].click();", first_item)

        # 9. Wait so you can see the selected account in the main navigation
        # nav_xpath = "//span[contains(@class,'js-primary-nav-address')]"
        # selected = False
        # for attempt in range(15):
        #     time.sleep(1)
        #     try:
        #         nav_texts = [" ".join((e.get_attribute("textContent") or "").split()).lower()
        #                      for e in driver.find_elements(By.XPATH, nav_xpath)]
        #     except StaleElementReferenceException:
        #         continue   # page is refreshing, try again
        #     if any(address.lower() in t for t in nav_texts):
        #         selected = True
        #         break


        nav_xpath = "//span[contains(@class,'js-primary-nav-address')]"
        selected = False
        for attempt in range(15):
            time.sleep(1)
            # try:
            #     nav_texts = [" ".join((e.get_attribute("textContent") or "").split()).lower()
            #                  for e in driver.find_elements(By.XPATH, nav_xpath)]
            # except StaleElementReferenceException:
            #     continue


            try:
                nav_texts = [" ".join((e.get_attribute("textContent") or "").split()).lower()
                             for e in driver.find_elements(By.XPATH, nav_xpath)]
            except StaleElementReferenceException:
                continue
            except NoSuchWindowException:
                print("Window closed. Windows left:", len(driver.window_handles))
                if driver.window_handles:
                    driver.switch_to.window(driver.window_handles[-1])
                    print("Switched to:", driver.current_url)
                    continue
                raise


            if any(address.lower() in t for t in nav_texts):
                selected = True
                break
            # still not selected after 5 seconds -> try the keyboard
            if attempt == 5:
                try:
                    first_item.send_keys(Keys.ENTER)
                except Exception:
                    pass


        if selected:
            print(f"Selected account shown in nav: {address}")
        else:
            print(f"Warning: nav did not show {address} - check the screenshot")
            driver.save_screenshot(f"nav_check_{acc_no}.png")

        time.sleep(5)




        billing_btn_xpath = "//li[@id='account_billing']/button"
        my_account_xpath = "//li[@id='account_billing']//a[@href='/en/accounts-billing/my-account']"

        billing_btn = wait.until(EC.presence_of_element_located((By.XPATH, billing_btn_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", billing_btn)

        # hover first
        ActionChains(driver).move_to_element(billing_btn).perform()
        time.sleep(1)

        # if hover did not open the dropdown, click the button
        links = [e for e in driver.find_elements(By.XPATH, my_account_xpath) if e.is_displayed()]
        if not links:
            ActionChains(driver).move_to_element(billing_btn).click().perform()
            time.sleep(1)

        # wait for the "My Account" link to be visible, then click it
        my_account_link = wait.until(lambda d: next(
            (e for e in d.find_elements(By.XPATH, my_account_xpath) if e.is_displayed()), False))
        print("Dropdown opened, clicking 'My Account'")
        try:
            ActionChains(driver).move_to_element(my_account_link).click().perform()
        except Exception:
            driver.execute_script("arguments[0].click();", my_account_link)

        # wait until the My Account page has loaded
        wait.until(EC.url_contains("/accounts-billing/my-account"))
        print("My Account page opened for:", acc_no, "|", driver.current_url)
        time.sleep(3)

        # 11. PDF download and rename will go here





        wait.until(EC.url_contains("/accounts-billing/my-account"))
        print("My Account page opened for:", acc_no, "|", driver.current_url)
        time.sleep(3)

        # ===== NEW CODE STARTS HERE (8 spaces of indentation, inside the try) =====

        # 11. Scroll to "View Current Bill (PDF)" and click it
        bill_xpath = ("//a[contains(@class,'js-bill-link')]"
                      "[.//span[contains(normalize-space(.),'View Current Bill')]]")

        bill_link = wait.until(EC.presence_of_element_located((By.XPATH, bill_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", bill_link)
        time.sleep(1)

        main_window = driver.current_window_handle
        windows_before = driver.window_handles


        pdf_url = bill_link.get_attribute("href") 


        print("Found bill link, clicking 'View Current Bill (PDF)'")
        try:
            ActionChains(driver).move_to_element(bill_link).click().perform()
        except Exception:
            driver.execute_script("arguments[0].click();", bill_link)
        time.sleep(3)

        # if the PDF opened in a new tab, look at it, then close it and come back
        windows_after = driver.window_handles
        if len(windows_after) > len(windows_before):
            new_tab = [w for w in windows_after if w not in windows_before][0]
            driver.switch_to.window(new_tab)
            print("Bill opened in new tab:", driver.current_url[:80])
            time.sleep(5)   # time for you to see the bill
            driver.close()
            driver.switch_to.window(main_window)
        else:
            print("No new tab opened (the PDF may have downloaded or opened in this tab)")




                # 12. Save the PDF as <account number>.pdf in SAVE_DIR
        save_path = os.path.join(SAVE_DIR, f"{acc_no}.pdf")
        try:
            req = urllib.request.Request(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                pdf_bytes = resp.read()

            if pdf_bytes[:4] == b"%PDF":
                with open(save_path, "wb") as f:
                    f.write(pdf_bytes)
                print(f"Saved bill for {acc_no}: {save_path}")
            else:
                print(f"Warning: downloaded data for {acc_no} is not a PDF, not saved")
        except Exception as e:
            print(f"Could not save PDF for {acc_no}: {type(e).__name__}: {e}")




    except TimeoutException:
        print(f"Error: timed out or no matching result for {acc_no}")
        driver.save_screenshot(f"timeout_{acc_no}.png")
        # Try clicking the body or escape to reset the dropdown state if it got stuck open
        try:
            driver.find_element(By.TAG_NAME, "body").click()
        except:
            pass
        continue

    except NoSuchWindowException:
        print(f"Window lost at {acc_no}. Windows left:", len(driver.window_handles))
        if driver.window_handles:
            driver.switch_to.window(driver.window_handles[-1])
            continue
        break

    except WebDriverException as e:
        print(f"Browser session error at {acc_no}: {type(e).__name__}")
        break


time.sleep(10)