from bs4 import BeautifulSoup
import glob, sys, os

VIEW_ROW_CLASS = 'AnswerViewsStatsRow'
UPVOTE_ROW_CLASS = 'AnswerUpvotesStatsRow'
QUESTION_LINK_CLASS = 'view_other_answers_link'

def get_answer_stats(filename):
  '''
    This function will parse all the statistics of a particular answer
    Args:
      filename - the full path of the downloaded answer file
    Returns:
      A list of 3 elements - views, upvotes, question_link
  '''
  fp = open(filename, 'r')
  doc = BeautifulSoup(fp.read(), 'html.parser')
  fp.close()

  # Parsing the View Count
  view_str = doc.find_all(class_=VIEW_ROW_CLASS)[0].strong.string
  views = int(view_str.replace(',', ''))

  # Parsing the Upvotes Count
  upvote_str = doc.find_all(class_=UPVOTE_ROW_CLASS)[0].strong.string
  upvotes = int(upvote_str.replace(',', ''))

  # Parsing the Question Link
  question_link = 'https://www.quora.com' + doc.find_all(
    class_=QUESTION_LINK_CLASS)[0].a.get('href')

  return [views, upvotes, question_link]

def parse_all_answers(directory, verbose=False):
  '''
    This function parses statistics for all the downloaded answers
    Args:
      directory - The full or relative path of the directory containing all the
                  downloaded answers
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
      answer_stat_list.append(get_answer_stats(filename))
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
