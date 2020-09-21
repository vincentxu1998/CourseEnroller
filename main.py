import logging

logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger()

from numpy import random

from retrying import retry

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time

COURSE_WEBPAGE = r"https://acorn.utoronto.ca/sws/#/courses/0"
USERNAME_XPATH = '//input[@id="username"]'
PASSWORD_XPATH = '//*[@id="password" and @name="j_password"]'
LOGIN_BUTTON_XPATH = '//button[contains(text(), "log in")]'



def logon_to_acorn(username, password):
    driver.get(COURSE_WEBPAGE)
    username_textinput = driver.find_element_by_xpath(USERNAME_XPATH)
    username_textinput.send_keys(username)
    password_textinput = driver.find_element_by_xpath(PASSWORD_XPATH)
    password_textinput.send_keys(password)
    login_button = driver.find_element_by_xpath(LOGIN_BUTTON_XPATH)
    login_button.click()
    driver.get(COURSE_WEBPAGE)

def course_in_enrolment_cart(course):
    my_enrolment_cart_xpath = '//div[@class="planningArea"]'
    course_plan_box = '//div[@class="coursePlan courseBox" and contains(@id, "{}")]'.format(course)
    xpath = my_enrolment_cart_xpath + course_plan_box
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        logger.info("{} not in enrolment cart!".format(course))
        return False
    logger.info("{} in enrolment cart!".format((course)))
    return True

def get_space_availability_texts(course, section):
    my_enrolment_cart_xpath = '//div[@class="planningArea"]'
    course_plan_box = '//div[@class="coursePlan courseBox" and contains(@id, "{}")]'.format(course)
    enrol_button = '//span[contains(text(), "Enrol") or contains(text(), "Waitlist")]'
    full_enrol_button = my_enrolment_cart_xpath + course_plan_box + enrol_button
    try:
        time.sleep(2)
        buttons = driver.find_elements_by_xpath(full_enrol_button)
        if len(buttons) <= 0:
            raise NoSuchElementException
    except NoSuchElementException:
        logger.info("{} cart enrol button not found".format(course))
        raise NoSuchElementException()
    for button in buttons:
        if button.is_displayed():
            button.click()
            logging.info("{} cart {} clicked".format(course, button.text))
        else:
            logging.info("{} cart {} not clicked".format(course, button.text))
    section_xpath = '//tbody[@id="{}"]'.format(section)
    space_availability_xpath = '//td[contains(@class, "spaceAvailability")]'
    full_space_availability_xpath = section_xpath + space_availability_xpath
    try:
        time.sleep(1)
        space_availability_elements = driver.find_elements_by_xpath(full_space_availability_xpath)
    except NoSuchElementException:
        logger.info("{} {} space availability not found".format(course, section))
        raise NoSuchElementException()
    logger.info("{} {} space availability found".format(course, section))
    space_availability_texts = [element.text for element in space_availability_elements]
    logger.info("{} {} : {}".format(course, section, space_availability_texts))
    return space_availability_texts

def check_space_availability(course, section):
    space_availability_texts = get_space_availability_texts(course, section)
    if len(space_availability_texts) == 0:
        raise Exception
    for text in space_availability_texts:
        if "of" in text and "available" in text:
            space_availability = int(text.split()[0].strip())
            logging.info("{} {} space availabity: {}!!!!!!!!!!!!!!!!!!"
                         "\n!!!!!!!!!!!!!!!!!Please Enrol Now!!!!!!!!!!!!!!!!!!!!!".format(course, section, space_availability))
            if space_availability > 0:
                return True
    logging.info("{} {} is not available: {}".format(course, section, space_availability_texts))
    return False

def click_circle(course, section):
    section_xpath = '//tbody[@id="{}"]'.format(section)
    circle_xpath = '//td[@class="activity"]//input[@type="radio"]'
    course_section_circle_xpath = section_xpath + circle_xpath
    try:
        driver.find_element_by_xpath(course_section_circle_xpath).click()
        logging.info("{} {} circle clicked".format(course, section))
    except Exception:
        logging.info("{} {} circle not found".format(course, section))


def enrol_popup_cancel():
    enrol_cancel_button_xpath = '//button[contains(text(), "Cancel")]'
    try:
        driver.find_element_by_xpath(enrol_cancel_button_xpath).click()
    except NoSuchElementException:
        logging.info("Popup Cancel Button not found")

def enrol_popup_approve():
    popup_approve_button_xpath = '//span[contains(text(), "Enrol")]'
    try:
        driver.find_element_by_xpath(popup_approve_button_xpath).click()
        logging.info("Popup Enrol Button clicked")
    except NoSuchElementException:
        logging.info("Popup Enrol Button not found")

def start_enrolment(username, password, course, section):
    logon_to_acorn(username, password)
    if course_in_enrolment_cart(course):
        i = 0
        while not check_space_availability(course, section):
            time.sleep(random.uniform(4, 6))
            click_circle(course, section)
            enrol_popup_cancel()
            time.sleep(random.uniform(2, 5))
            if i%15 == 0:
                driver.refresh()
            i += 1
        click_circle(course, section)
        enrol_popup_approve()

@retry(wait_fixed=1000)
def main(username, password, course, section):
    try:
        global driver
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        start_enrolment(username, password, course, section)
    except Exception:
        driver.close()
        raise Exception



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Course Enrol Robot')
    parser.add_argument('-u', '--username', help='Please enter your username', required=True)
    parser.add_argument('-p', '--password', help='Please enter your password', required=True)
    parser.add_argument('-c', '--course', help='Course must be exactly same as the name in enrolment cart. Require course to be added into enrolment cart', required=True)
    parser.add_argument('-s', '--section', help='Require - in section name. e.g LEC-0101', required=True)
    args = parser.parse_args()
    main(args.username, args.password, args.course, args.section)



