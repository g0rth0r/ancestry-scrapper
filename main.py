from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os, base64, re, pathlib, shutil, time, glob, json, datetime
from dotenv import load_dotenv
from selenium.webdriver.chrome.options import Options

load_dotenv()

LOGIN = os.getenv("LOGIN")
PASS = os.getenv("PASS")
LOGIN_URL = "https://www.ancestry.ca/account/signin"
TEST_APID = "1,8826::13093148"
TEST_APID_LIST = ["1,8826::14443827", "1,8826::13093148"]
BASE_DIR = "sources"

DOWNLOAD_DIR = "downloads"
CUR_DIR = pathlib.Path().absolute()
DOWN_PATH = os.path.join(CUR_DIR, DOWNLOAD_DIR)

GEDCOM = os.getenv("GED_FILE")

def get_source_url(apid):
    ids = re.findall(r"[\w']+", apid)
    print(ids)

    return "https://search.ancestry.ca/cgi-bin/sse.dll?indiv={}&dbid={}&h={}".format(ids[0], ids[1], ids[2])

class Driver(object):
    def __init__(self, user, pwd):
        self.preferences = {"download.default_directory": DOWN_PATH,  # pass the variable
                       "download.prompt_for_download": False,
                       "directory_upgrade": True,
                       "safebrowsing.enabled": True}
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option("prefs", self.preferences)

        #self.options.add_argument("download.default_directory=" + DOWN_PATH)
        self.driver = webdriver.Chrome(chrome_options=self.options)


        self.user = user
        self.pwd = pwd

        # assert "Sign In" in driver.title

    def do_login(self):
        """Login to get a session."""
        self.driver.get(LOGIN_URL)
        self.driver.get(LOGIN_URL)
        self.driver.implicitly_wait(5)
        self.driver.find_element(By.XPATH, '//*[@id="Banner_cookie_0"]/div[2]/div/div[2]/div/button[1]').click()

        #Fill login info
        print("[*] Filling Login Info...")

        actions = ActionChains(self.driver)
        actions.send_keys(Keys.TAB)
        actions.send_keys(Keys.TAB)
        actions.send_keys(self.user)
        actions.send_keys(Keys.TAB)
        actions.send_keys(self.pwd)
        actions.send_keys(Keys.TAB)
        actions.send_keys(Keys.ENTER)
        actions.perform()

        #WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
        #    (By.XPATH, '//*[@id="destination_publishing_iframe_ancestry-mcsp_0"]')))

        #self.driver.switch_to.frame(self.driver.find_element_by_xpath('//*[@id="destination_publishing_iframe_ancestry-mcsp_0"]'))
        # //*[@id="destination_publishing_iframe_ancestry-mcsp_0"]

        #username = self.driver.find_element(By.XPATH, '//*[@id="username"]')
        #username.send_keys(self.user)

        #password = self.driver.find_element(By.XPATH, '//*[@id="password"]')
        #password.send_keys(self.pwd)

        myElem = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="nav"]')))

    def parse_path(self, apid, filename):
        folder = base64.urlsafe_b64encode(apid.encode('utf-8'))
        full_path = os.path.join(BASE_DIR, folder.decode('utf-8'), filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

    def get_print_version_from_source(self, apid):
        # print = WebDriverWait(self.driver, 20).until(
        #    EC.element_to_be_clickable((By.XPATH, '//*[@id="mainContent"]/div/header/div/a')))

        # OPen Print Friendly Source Page
        # print.click()

        # Switch to the new tab and wait for it to load
        #self.driver.switch_to.window(self.driver.window_handles[-1])

        # ready = WebDriverWait(self.driver, 20).until(
        #    EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]')))

        with open(self.parse_path(apid, "source_desc.html"), "wb") as f:
            f.write(self.driver.page_source.encode('utf-8'))

        # Close Tab
        # self.driver.close()
        # self.driver.switch_to.window(self.driver.window_handles[0])

    def get_scan_from_source(self):

        view = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '// *[ @ id = "viewOriginal"] / span')))
        view.click()

        tools = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/div/div/div/div[1]/div[3]/button[3]')))
        tools.click()

        download = ActionChains(self.driver)
        download.send_keys(Keys.TAB)
        download.send_keys(Keys.TAB)
        download.send_keys(Keys.ENTER)
        download.perform()

        file = self.monitor_download()

        return file

    def source_scrapper_handler(self, apid):

        data = {}
        data['time'] = datetime.datetime.now()
        data['apid'] = apid
        data['url'] = get_source_url(apid)


        try:
            self.go_to_source_page(apid)
        except:
            data['msg'] = "Could not load source url."

        try:
            self.get_print_version_from_source(apid)
        except:
            data['msg'] = "Could not load or save printable source."

        try:
            file = self.get_scan_from_source()
            data['file'] = file
            data['msg'] = "OK"
        except:
            data['msg'] = "Could not retrieve source scan."

        with open(self.parse_path(apid, "info.json"), "w") as f:
            json.dump(data, f, indent=4, sort_keys=True, default=str)

    def go_to_source_page(self, apid):
        self.driver.get(get_source_url(apid))

    def load_source(self, apid):

        self.driver.get(get_source_url(apid))

        # Print page:
        print = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="mainContent"]/div/header/div/a')))

        # OPen Print Friendly Source Page
        print.click()
        # //*[@id="mainContent"]

        # Switch to the new tab and wait for it to load
        self.driver.switch_to.window(self.driver.window_handles[-1])


        ready = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]')))

        with open(self.parse_path(apid, "source_desc.html"), "wb") as f:
            f.write(self.driver.page_source.encode('utf-8'))

        # Close Tab
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        # Download Source Scan

        view = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '// *[ @ id = "viewOriginal"] / span')))
        view.click()

        tools = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/div/div/div/div[1]/div[3]/button[3]')))
        tools.click()

        download = ActionChains(self.driver)
        download.send_keys(Keys.TAB)
        download.send_keys(Keys.TAB)
        download.send_keys(Keys.ENTER)
        download.perform()

        file = self.monitor_download()

        # Data to save as json about the scrap
        data = {"time": datetime.datetime.now(),
                "file": file,
                "apid": apid}

        with open(self.parse_path(apid, "info.json"), "w") as f:
            json.dump(data, f, indent=4, sort_keys=True, default=str)


    def monitor_download(self):
        wait_on_download = True
        time.sleep(1)
        while wait_on_download:
            list_of_files = glob.glob(DOWN_PATH + "\\*")
            latest_file = max(list_of_files, key=os.path.getctime)
            if ".crdownload" in latest_file:
                time.sleep(1)
                continue
            else:
                return latest_file.split("\\")[-1]


#TODO Function to parse GED file and get _APID into scrappable URL
def extract_apid_from_gedcom(ged):
    apid_list = set()

    with open(ged) as f:
        for line in f:
            l = line.rstrip("\n").split(" ")
            if l[1] == "_APID":
                apid_list.add(l[2])

    return apid_list




if __name__ == "__main__":
    to_extract = extract_apid_from_gedcom(GEDCOM)
    chrome = Driver(LOGIN, PASS)
    chrome.do_login()


    for apid in to_extract:
        print('[*] Scraping _APID = ' + apid)
        folder = base64.urlsafe_b64encode(apid.encode('utf-8'))
        if os.path.exists(os.path.join(BASE_DIR, folder.decode('utf-8'))):
            print("[!] APID Already scrapped. Skipping.")
        else:
            chrome.source_scrapper_handler(apid)






