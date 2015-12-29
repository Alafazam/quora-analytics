from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException as STException
import pickle, time, os, re, urllib2, errno
import pdfkit

LOGIN_FORM_SELECTOR = '.inline_login_form'
ERROR_MSG_SELECTOR = '.input_validation_error_text[style*="display: block"]'
CONTENT_PAGE_ITEM_SELECTOR = '.UserContentList .pagedlist_item'
QUORA_TITLE = 'Quora - The best answer to any question'
HOME_TITLE = 'Quora - Home'
CONTENT_TILE = 'Your Content - Quora'
CONTENT_URL = 'https://www.quora.com/content?content_types=answers'
PROFILE_IMG_SELECTOR = '.nav_item_link .expanded .profile_photo_img'
# Adjust this if your Internet connection is slow. It is used to scroll answers
JS_SCROLL_TIMEOUT = 2 # In seconds

# Given origin (timestamp offset by time zone) and string from Quora, e.g.
# "Added 31 Jan", returns a string such as '2015-01-31'.
# Quora's short date strings don't provide enough information to determine the
# exact time, unless it was within the last day, so we won't bother to be any
# more precise.
def parse_quora_date(quora_str):
  origin = time.time() - time.timezone
  days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  months_of_year = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  _, _, date_str = quora_str.partition('Added ')
  date_str = date_str.strip()
  if date_str == '':
    raise ValueError('"%s" does not appear to indicate when answer was added' % quora_str)
  m0 = re.match('just now$', date_str)
  m1 = re.match('(\d+)m ago$', date_str)
  m2 = re.match('(\d+)h ago$', date_str)
  m3 = re.match('(' + '|'.join(days_of_week) + ')$', date_str)
  m4 = re.match('(' + '|'.join(months_of_year) + ') (\d+)$', date_str)
  m5 = re.match('(' + '|'.join(months_of_year) + ') (\d+), (\d+)$', date_str)
  m6 = re.match('(\d+)[ap]m$', date_str)
  if not m0 is None or not m6 is None:
    # Using origin for time in am / pm since the time of the day will be discarded anyway
    tm = time.gmtime(origin)
  elif not m1 is None:
    tm = time.gmtime(origin - 60*int(m1.group(1)))
  elif not m2 is None:
    tm = time.gmtime(origin - 3600*int(m2.group(1)))
  elif not m3 is None:
    # Walk backward until we reach the given day of the week
    day_of_week = days_of_week.index(m3.group(1))
    offset = 1
    while offset <= 7:
      tm = time.gmtime(origin - 86400*offset)
      if tm.tm_wday == day_of_week:
        break
      offset += 1
    else:
      raise ValueError('date "%s" is invalid' % date_str)
  elif not m4 is None:
    # Walk backward until we reach the given month and year
    month_of_year = months_of_year.index(m4.group(1)) + 1
    day_of_month = int(m4.group(2))
    offset = 1
    while offset <= 366:
      tm = time.gmtime(origin - 86400*offset)
      if tm.tm_mon == month_of_year and tm.tm_mday == day_of_month:
        break
      offset += 1
    else:
      raise ValueError('date "%s" is invalid' % date_str)
  elif not m5 is None:
    # may raise ValueError
    tm = time.strptime(date_str, '%b %d, %Y')
  else:
    raise ValueError('date "%s" could not be interpreted' % date_str)
  return '%d-%02d-%02d' % (tm.tm_year, tm.tm_mon, tm.tm_mday)

class QuoraCrawler(object):

  PHANTOMJS_DRIVER = 0
  CHROME_DRIVER = 1
  FIREFOX_DRIVER = 2
  SAVE_AS_HTML= 0
  SAVE_AS_PDF= 1

  class InvalidCredentialException(Exception):
    pass

  def __init__(self, answer_list_file_path='answers.dat',
    cookie_path='user-data/phantomja/phantom-cookie',
    driver=PHANTOMJS_DRIVER,
    user_dir='user-data/chrome-user-data'):
    self.answer_list = None
    self.answer_file_path = answer_list_file_path

    # Setting Answer List by reading from file
    if os.path.isfile(answer_list_file_path):
      try:
        with open(answer_list_file_path, 'rb') as answer_file:
          self.answer_list = pickle.load(answer_file)
      except (ValueError, pickle.UnpicklingError, AttributeError, EOFError,
              IndexError):
        print "Value Error"
        self.answer_list = []
    if not self.validate_answer_list(): self.answer_list = []

    # Initializing Driver
    if driver == self.PHANTOMJS_DRIVER:
      self.driver = webdriver.PhantomJS(
        service_args=['--remote-debugger-port=9000',
                      '--ssl-protocol=any',
                      '--cookies-file=' + cookie_path])
    elif driver == self.CHROME_DRIVER:
      co = webdriver.ChromeOptions()
      co.add_argument("--user-data-dir=" + user_dir)
      self.driver = webdriver.Chrome(chrome_options=co)
    elif driver == self.FIREFOX_DRIVER:
      self.driver = webdriver.Firefox()


    # Setting Driver Window Size - Known Hack for a Bug.
    self.driver.set_window_size(1120, 550)

  def reset_answer_list(self):
    self.answer_list = []
    self.write_answer_file()

  def validate_answer_list(self):
    if self.answer_list is None or type(self.answer_list) != list: return False
    for e in self.answer_list:
      if type(e) != list or len(e) != 3:
        return False
      for item in e:
        if type(item) not in (str, unicode): return False
    return True

  def write_answer_file(self):
    with open(self.answer_file_path, 'wb') as answer_file:
      pickle.dump(self.answer_list, answer_file)

  def _is_new_answer(self, old_ans_length):
    '''
      This function returns True if any new answer is available on page or if no
      more new answers can fetched - i.e., are we done scrolling ?
    '''
    elements = self.driver.find_elements_by_css_selector(
      CONTENT_PAGE_ITEM_SELECTOR)

    len_new = len(elements[old_ans_length:])
    if len_new > 0:
      return True
    spinner_display = self.driver.find_element_by_css_selector(
      '.pager_next[id$="loading"]').value_of_css_property('display')
    if spinner_display != 'none':
      return False

    len_hidden = len(self.driver.find_elements_by_css_selector(
      '.pagedlist_item[style*="display: none"]'))
    if len_hidden == 0:
      len_hidden = len(self.driver.find_elements_by_class_name(
        'pagelist_hidden'))
    return len_hidden == 0

  def logout(self, prog=None, status=None):
    if 'Quora' not in self.driver.title:
      self.driver.get('https://www.quora.com/')
      WebDriverWait(self.driver, 10)

    if QUORA_TITLE not in self.driver.title:
      self.driver.find_element_by_css_selector(
        "form[id$='_logout_form']").submit()
      WebDriverWait(self.driver, 10)

  def check_login(self, prog=None, status=None):
    if 'Quora' not in self.driver.title:
      self.driver.get('https://www.quora.com/')
      WebDriverWait(self.driver, 10)
      print 'Quora is open'
    else:
      return QUORA_TITLE not in self.driver.title

  def get_user_name(self):
    # assert self.check_login()
    return self.driver.find_element_by_css_selector(
      PROFILE_IMG_SELECTOR).get_attribute('alt')

  def login(self, email, password, prog=None, status=None):
    if self.check_login(prog, status):
      return
    # Make Sure we are on Login Page
    # assert QUORA_TITLE in self.driver.title

    print 'We have to login with email and password'
    email_input = self.driver.find_element_by_css_selector(
      LOGIN_FORM_SELECTOR + ' input[type=text]')
    password_input = self.driver.find_element_by_css_selector(
      LOGIN_FORM_SELECTOR + ' input[type=password]')

    # assert email_input.is_displayed() and email_input.is_enabled()
    # assert password_input.is_displayed() and password_input.is_enabled()

    print 'input login details'
    email_input.clear()
    password_input.clear()
    email_input.send_keys(email)
    password_input.send_keys(password + Keys.RETURN)

    print 'wait for login'
    WebDriverWait(self.driver, 10)



    if 'Home - Quora' not in self.driver.title:
      raise self.InvalidCredentialException('Invalid Login Credentials')
    else:
      print "Successfully Logged In"

  def scroll_page(self):
    # Executing JavaScript function to scroll page
    self.driver.execute_script("""
      document.body.scrollTop = document.body.scrollTop + 10000;
    """)

  @property
  def no_of_answers(self):
    return self.driver.execute_script("""
      return $('%s').length;
    """ % CONTENT_PAGE_ITEM_SELECTOR)

  def update_answer_list(self, prog=None, status=None):
    if CONTENT_TILE not in self.driver.title:
      # Navigate to Content Page
      self.driver.get(CONTENT_URL)
      WebDriverWait(self.driver, 10)
    print 'Content page loaded'

    new_answer_exist = True
    new_answer_list = []
    while new_answer_exist:
      time.sleep(2)
      self.scroll_page() # Scrolling the page to load more answers
      try:
        WebDriverWait(self.driver, 20).until(
          lambda x: len(x.find_elements_by_css_selector(
            CONTENT_PAGE_ITEM_SELECTOR)[len(new_answer_list):]) > 0)
      except STException:
        print "Exception Received"
        self.scroll_page() # Scrolling the page to load more answers
        time.sleep(2)
        pass
      print "Page Scrolling Successful"
      # Parsing the answers fetched
      elements = self.driver.find_elements_by_css_selector(
        CONTENT_PAGE_ITEM_SELECTOR);
      print 'all answer elements found'

      print 'Fetched ' + str(len(elements)) + ' answers'


      # Iterating over only new elements fetched in this cycle
      elements = elements[len(new_answer_list):]
      for element in elements:
        link = element.find_element_by_tag_name('a').get_attribute('href')
        if len(self.answer_list) > 0 and link == self.answer_list[0][0]:
          # The remaining answer links are already available in answer_list
          new_answer_list.extend(self.answer_list)
          new_answer_exist = False
          break
        else:
          ques = element.find_element_by_class_name('rendered_qtext').text
          time_text = element.find_element_by_class_name(
            'metadata').get_attribute('innerHTML')
          new_answer_list.append([link, parse_quora_date(time_text), ques])

      if len(elements) == 0:
        # If no new item answer was fetched in this cycle
        print "No More Answers to fetch"
        new_answer_exist = False

    # Writing the updated answer list to file
    self.answer_list = new_answer_list
    self.write_answer_file()
    print 'answers file saved'


  def download_answers(self, directory='quora-answers',
    update_answer=True, overwrite=False, delay=0):
    # Update answer List if required
    if update_answer:
      self.update_answer_list()

    # Creating necessary directory
    try:
      os.mkdir(directory, 0o700)
    except OSError as error:
      if error.errno != errno.EEXIST:
        raise

    print 'now saving the answers'
    os.chdir(directory)
    download_file_count = 0
    for idx, e in enumerate(self.answer_list):
      # Get the part of the URL indicating the question title
      m1 = re.search('quora\.com/([^/]+)/answer', e[0])
      # if there's a context topic
      m2 = re.search('quora\.com/[^/]+/([^/]+)/answer', e[0])
      filename = e[1] + ' '
      if not m1 is None:
        filename += m1.group(1)
      elif not m2 is None:
        filename += m2.group(1)
      else:
        filename = 'could_not_parse_filename' + str(idx)

      # Trim the filename if it's too long. 255 bytes is the limit on many filesystems.
      total_length = len(filename + '.html')
      if len(filename + '.html') > 255:
        filename = filename[:(255 - len(filename + '.html'))]
      filename += '.html'

      # If overwrite is enabled or the answer doesn't exist
      if overwrite or not os.path.isfile(filename):
        # Fetch the URL to find the answer
        try:
          self.save_answer(e[0], filename, save_as=SAVE_AS_HTML)
          download_file_count += 1
          print 'answer '+ str(e[0]) + ' saved as ' + filename + '' + SAVE_AS_HTML
        except urllib2.URLError as error:
          print '[ERROR] Failed to download answer from URL %s (%s)' % (url, error.reason)
          continue
        except IOError as error:
          print '[ERROR] Failed to save answer to file %s (%s)' % (filename, error.strerror)

        time.sleep(delay)

  def save_answer(self, url, filename, save_as):
    if save_as == self.SAVE_AS_HTML:
      page_html = urllib2.urlopen(url).read()
      with open(filename, 'wb') as f:
        f.write(page_html)
    elif save_as == self.SAVE_AS_PDF:
      pdfkit.from_url(url, filename)

  def quit(self):
    self.driver.quit()

if __name__ == '__main__':
  rc = QuoraCrawler(driver=QuoraCrawler.FIREFOX_DRIVER)
  rc.login(os.environ['QUORA_USERNAME'], os.environ['QUORA_PASSWORD'])
  answer_list = rc.download_answers()
  rc.quit()
