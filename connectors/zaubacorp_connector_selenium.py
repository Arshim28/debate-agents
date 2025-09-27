from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
from typing import Dict, List, Optional
import json 
from pydantic import BaseModel
from google.genai import types
from google import genai

class OtherDirectorships(BaseModel):
    director_name: str
    other_directorships: list[str]

class DirectorInfo(BaseModel):
    current_directors: list[str]
    past_directors: list[str]
    other_directorships: list[OtherDirectorships]

class ZaubaCorpSelenium:
    def __init__(self, gemini_api_key, headless: bool = True, timeout: int = 10, implicit_wait: int = 5):
        self.headless = headless
        self.timeout = timeout
        self.implicit_wait = implicit_wait
        self.driver = None
        self.gemini_client = genai.Client(api_key=gemini_api_key)
    
    def _setup_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(self.implicit_wait)
        return driver
    
    def get_cookies(self, url: str, wait_time: Optional[int] = None) -> List[Dict]:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            self.driver = self._setup_driver()
            self.driver.get(url)
            
            if wait_time:
                time.sleep(wait_time)
            else:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            
            cookies = self.driver.get_cookies()
            return cookies
            
        except TimeoutException:
            print(f"Timeout while loading {url}")
            return []
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return []
        except Exception as e:
            print(f"Error collecting cookies from {url}: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    
    def get_cookies_with_actions(self, url: str, actions_callback=None) -> List[Dict]:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            self.driver = self._setup_driver()
            self.driver.get(url)
            
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            if actions_callback and callable(actions_callback):
                actions_callback(self.driver)
            
            cookies = self.driver.get_cookies()
            return cookies
            
        except TimeoutException:
            print(f"Timeout while loading {url}")
            return []
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return []
        except Exception as e:
            print(f"Error collecting cookies from {url}: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    
    def format_cookies_for_requests(self, cookies: List[Dict]) -> Dict[str, str]:
        return {cookie['name']: cookie['value'] for cookie in cookies}
    
    def cookies_to_string(self, cookies: List[Dict]) -> str:
        return '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
    
    def _filter_director_info(self, director_information):
        input_prompt = f"""
        You are given an HTML snippet containing information about the directors of a company. Extract the following information from the HTML only:
            - Names of current directors
            - Names of past directors
            - Other companies where each director (current or past) is or was a director
        
        The Other Directorships should only contain directors who have other directorships if no other directorships then they should not be present in the list.
        
        Return the extracted information in a json format:
        {{
            "current_directors": ["Director 1", "Director 2"],
            "past_directors": ["Former Director 1", "Former Director 2"],
            "other_directorships": [
            {{ "Director 1": ["Company A", "Company B"]}},
            {{ "Director 2": ["Company C"]}},
            {{ "Former Director 1": ["Company D"]}}
            ]
        }}

        Notes:
        Only extract information present in the HTML snippet. Do not make assumptions or fetch data from external sources.
        If any field is missing, return it as an empty list or empty object.
        Ensure the JSON is valid and properly parsable.

        HTML snippet:
        {director_information}
        """
        print("Extracting director information from HTML snippet")
        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=input_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DirectorInfo,
            )
        )
        return json.loads(response.text)

    def search_company_and_get_director_info(self, company_name: str) -> Optional[str]:
        try:
            self.driver = self._setup_driver()
            self.driver.get("https://www.zaubacorp.com/")
            
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "searchid"))
            )
            
            search_input = self.driver.find_element(By.ID, "searchid")
            search_input.clear()
            search_input.send_keys(company_name)
            
            time.sleep(1)
            
            try:
                suggestions_container = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "result"))
                )
                
                suggestion_items = suggestions_container.find_elements(By.CSS_SELECTOR, "div, li, a")
                
                if suggestion_items:
                    print(f"Found {len(suggestion_items)} suggestions")
                    first_suggestion = suggestion_items[0]
                    print(f"Clicking on suggestion: {first_suggestion.text[:100]}")
                    
                    self.driver.execute_script("arguments[0].click();", first_suggestion)
                    
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    time.sleep(2)
                    
                else:
                    print("No suggestions found, submitting form directly")
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.form-submit")
                    submit_button.click()
                    
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    time.sleep(2)
                    
            except TimeoutException:
                print("No autocomplete suggestions appeared, submitting form directly")
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.form-submit")
                submit_button.click()
                
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                time.sleep(2)
            
            try:
                director_info_element = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.ID, "director-information"))
                )
                return self._filter_director_info(director_info_element.get_attribute('outerHTML'))
            except TimeoutException:
                print("Director information section not found on the page")
                return None
                
        except TimeoutException:
            print(f"Timeout while searching for company: {company_name}")
            return None
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return None
        except Exception as e:
            print(f"Error searching for company {company_name}: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
    
    def search_company_and_get_full_page(self, company_name: str) -> Optional[str]:
        try:
            self.driver = self._setup_driver()
            self.driver.get("https://www.zaubacorp.com/")
            
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "searchid"))
            )
            
            search_input = self.driver.find_element(By.ID, "searchid")
            search_input.clear()
            search_input.send_keys(company_name)
            
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.form-submit")
            submit_button.click()
            
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(3)
            
            return self.driver.page_source
                
        except TimeoutException:
            print(f"Timeout while searching for company: {company_name}")
            return None
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return None
        except Exception as e:
            print(f"Error searching for company {company_name}: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
    
    def search_with_autocomplete_and_extract(self, company_name: str, target_div_id: str = "director-information") -> Optional[str]:
        try:
            self.driver = self._setup_driver()
            self.driver.get("https://www.zaubacorp.com/")
            
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "searchid"))
            )
            
            search_input = self.driver.find_element(By.ID, "searchid")
            search_input.clear()
            search_input.send_keys(company_name)
            
            time.sleep(2)
            
            try:
                suggestions_container = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.ID, "result"))
                )
                
                time.sleep(1)
                
                clickable_suggestions = suggestions_container.find_elements(By.CSS_SELECTOR, "div[onclick], a, div[style*='cursor'], div[class*='suggestion'], div[class*='result']")
                
                if not clickable_suggestions:
                    clickable_suggestions = suggestions_container.find_elements(By.CSS_SELECTOR, "div")
                
                if clickable_suggestions:
                    print(f"Found {len(clickable_suggestions)} autocomplete suggestions")
                    
                    for i, suggestion in enumerate(clickable_suggestions[:3]):
                        print(f"Suggestion {i+1}: {suggestion.text[:100]}")
                    
                    first_suggestion = clickable_suggestions[0]
                    print(f"Clicking on first suggestion: {first_suggestion.text}")
                    
                    try:
                        first_suggestion.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", first_suggestion)
                    
                    WebDriverWait(self.driver, self.timeout).until(
                        lambda driver: driver.current_url != "https://www.zaubacorp.com/"
                    )
                    
                    time.sleep(3)
                    
                    print(f"Navigated to: {self.driver.current_url}")
                    
                else:
                    print("No clickable suggestions found, submitting form")
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.form-submit")
                    submit_button.click()
                    
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    time.sleep(3)
                    
            except TimeoutException:
                print("No autocomplete container found, submitting form directly")
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.form-submit")
                submit_button.click()
                
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                time.sleep(3)
            
            try:
                target_element = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.ID, target_div_id))
                )
                print(f"Found target div with ID: {target_div_id}")
                return target_element.get_attribute('outerHTML')
            except TimeoutException:
                print(f"Target div with ID '{target_div_id}' not found on the page")
                print("Available div IDs on the page:")
                divs_with_ids = self.driver.find_elements(By.CSS_SELECTOR, "div[id]")
                for div in divs_with_ids[:10]:
                    print(f"  - {div.get_attribute('id')}")
                return None
                
        except TimeoutException:
            print(f"Timeout while searching for company: {company_name}")
            return None
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return None
        except Exception as e:
            print(f"Error searching for company {company_name}: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    import os 
    from dotenv import load_dotenv
    load_dotenv()

    scraper = ZaubaCorpSelenium(gemini_api_key=os.getenv("GEMINI_API_KEY"), headless=False)
    
    company_name = "ZETWERK MANUFACTURING BUSINESSES PRIVATE LIMITED"
    print(f"Searching for company: {company_name}")
    
    director_info = scraper.search_company_and_get_director_info(company_name)
    if director_info:
        print("Director information found:")
        print(director_info)
    else:
        print("No director information found or company not found")