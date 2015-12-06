from bs4 import BeautifulSoup
import glob, sys, os, string

# Global constants for classes because this may change in future
VIEW_ROW_CLASS = 'AnswerViewsStatsRow'
UPVOTE_ROW_CLASS = 'AnswerUpvotesStatsRow'
QUESTION_LINK_CLASS = 'view_other_answers_link'
ANSWER_CONTENT_SELECTOR = '.ExpandedQText.ExpandedAnswer'
ANSWER_FOOTER_SELECTOR = '.ContentFooter.AnswerFooter'

def get_word_list(doc):
  '''
    This function will parse the text content of an answer and return the answer
    in form of a list of words
    Args:
      doc = BeautifulSoup Document
    Return:
      A list of words in the answer
  '''
  answer = doc.select(ANSWER_CONTENT_CLASS)[0]
  # We want only text content. So remove codes if any
  answer.code.decompose()

  # Remove the Answer Footer
  answer.select(ANSWER_FOOTER_SELECTOR)[0].decompose()

  # Parse the text content and separate each tag with space. Filter out spaces
  answer_text = answer.getText(separator=u' ').replace('.', ' ')
  wlist = re.sub('\s+', ' ', answer_text).split()

  # Filtering all the words with only punctuations since those are not words
  return filter(lambda x: len(x.translate(None, string.punctuation)) > 0, wlist)

def parse_answer(filename):
  '''
    This function will parse all the statistics of a particular answer
    Args:
      filename - the path of the downloaded answer file
    Returns:
      A list of 3 elements - views, upvotes, question_link
  '''
  fp = open(filename, 'r')
  doc = BeautifulSoup(fp.read(), 'html.parser')
  fp.close()

  parsed_answer = []

  # Parsing the View Count
  view_str = doc.find_all(class_=VIEW_ROW_CLASS)[0].strong.string
  parsed_answer.append(int(view_str.replace(',', '')))

  # Parsing the Upvotes Count
  upvote_str = doc.find_all(class_=UPVOTE_ROW_CLASS)[0].strong.string
  parsed_answer.append(int(upvote_str.replace(',', '')))

  # Parsing the Question Link
  question_link = 'https://www.quora.com' + doc.find_all(
    class_=QUESTION_LINK_CLASS)[0].a.get('href')
  parsed_answer.append(question_link)

  # Parsing Answer content in form of word list
  parsed_answer.append(get_word_list(doc))

  return parsed_answer

def parse_all_answers(directory, verbose=False):
  '''
    This function parses statistics for all the downloaded answers
    Args:
      directory - The path of the directory containing all the downloaded
                  answers
    Returns:
      A list of list with each inner list representing statistic of an answer
  '''
  # Getting all the html files in the answer directory
  file_list = glob.glob(os.path.join(directory, '*.html'))
  if verbose:
    print('Found %d downloaded answers !!' % len(file_list))

  answer_stat_list = []
  answers_parsed = 0
  for filename in file_list:
    # Processing the answer in filename
    try:
      answer_stat_list.append(parse_answer(filename))
      answers_parsed += 1
      if verbose:
        sys.stdout.write('\rNumber of Files Parsed = %d' % answers_parsed)
        sys.stdout.flush()
    except IndexError, ValueError:
      '''
        Index Error May be generated if no element with given class is found
        Value Error may be generated if non - integral values in views / upvotes
        This indicates that the Answer Page format has probably changed since
        this script was written. We will just skip this answer and move on
      '''
      sys.stderr.write(
        '[Error] : Unable to parse file %s. Skipping it.\n' % filename,
        file=sys.stderr
      )
  if verbose:
    sys.stdout.write('\n')
    sys.stdout.flush()

  return answer_stat_list
