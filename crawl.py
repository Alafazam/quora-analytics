from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json, time, os, re, urllib2, errno

LOGIN_FORM_SELECTOR = '.inline_login_form'
CONTENT_PAGE_ITEM_SELECTOR = '.UserContentList .pagedlist_item'
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
  print quora_str.partition('Added ')
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
  def __init__(self, answer_list_file_path='answers.json'):
    self.driver = driver = webdriver.PhantomJS(service_args=['--remote-debugger-port=9000'])
    driver.set_window_size(1120, 550)
    if os.path.isfile(answer_list_file_path):
      with open(answer_list_file_path, 'r') as answer_file:
        self.answer_list = json.load(answer_file)
    else:
        self.answer_list = []

  def write_answer_file(self, filepath='answers.json'):
    with open(filepath, 'w') as answer_file:
      json.dump(self.answer_list, answer_file)

  def login(self, email, password):
    self.driver.get('https://www.quora.com/')
    # Just asserting that we got the right page
    assert 'Quora' in self.driver.title

    email_input = self.driver.find_element_by_css_selector(
      LOGIN_FORM_SELECTOR + ' input[type=text]')
    password_input = self.driver.find_element_by_css_selector(
      LOGIN_FORM_SELECTOR + ' input[type=password]')
    email_input.send_keys(email)
    password_input.send_keys(password + Keys.RETURN)
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

  def update_answer_list(self):
    time.sleep(3)
    self.driver.get('https://www.quora.com/content?content_types=answers')
    print "Sleeping"
    time.sleep(5)
    print self.driver.title

    # Just Asserting that we got the right page
    assert 'Your Content - Quora' in self.driver.title

    new_answer_exist = True
    new_answer_list = []
    while new_answer_exist:
      self.scroll_page() # Scrolling the page to load more answers
      time.sleep(JS_SCROLL_TIMEOUT) # Sleeping while the page loads more answers

      # Parsing the answers fetched
      elements = self.driver.find_elements_by_css_selector(CONTENT_PAGE_ITEM_SELECTOR);

      # Iterating over only new elements fetched in this cycle
      elements = elements[len(new_answer_list)]
      for element in elements:
        link = element.find_element_by_tag_name('a').get_attribute('href')
        if len(self.answer_list) > 0 and link == self.answer_list[0][0]:
          # The remaining answer links are already available in answer_list
          new_answer_list.extend(self.answer_list)
          new_answer_exist = False
          break
        else:
          time_text = element.find_element_by_class_name('metadata').get_attribute('innerHTML')
          print 'time att= ', element.find_element_by_class_name('metadata').get_attribute('innerHTML')
          new_answer_list.append([link, parse_quora_date(time_text)])

      if len(elements) == 0:
        # If no new item answer was fetched in this cycle
        new_answer_exist = False

    # Writing the updated answer list to file
    self.answer_list = new_answer_list
    self.write_answer_file()

  def download_answers(self, directory='quora-answers', update_answer=True,
                      overwrite=False, delay=0):
    # Update answer List if required
    if update_answer:
      self.update_answer_list()

    # Creating necessary directory
    try:
      os.mkdir(directory, 0o700)
    except OSError as error:
      if error.errno != errno.EEXIST:
        raise

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
          page_html = urllib2.urlopen(e[0]).read()
          with open(filename, 'wb') as f:
            f.write(page_html)
          download_file_count += 1
        except urllib2.URLError as error:
          print '[ERROR] Failed to download answer from URL %s (%s)' % (url, error.reason)
          continue
        except IOError as error:
          print '[ERROR] Failed to save answer to file %s (%s)' % (filename, error.strerror)

        time.sleep(delay)

  def quit(self):
    self.driver.quit()

rc = QuoraCrawler()
try:
  rc.login(os.environ['QUORA_USERNAME'], os.environ['QUORA_PASSWORD'])
  answer_list = rc.download_answers()
except AssertionError:
  print "Some problem fetching the right content"
except Exception as e:
  rc.quit()
  print e
  raise e
rc.quit()
