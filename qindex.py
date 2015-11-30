import argparse
from parser import *

def compute_qindex(answer_stat_list, verbose=False):
  '''
    This function computes the qindex
    Args:
      answer_stat_list : A list of list representing statistics of all answers
    Return:
      QIndex : An integer representing QIndex of the User
  '''
  if len(answer_stat_list) == 0:
    return 0

  # Sorting the answers in descending order of upvotes
  answer_stat_list.sort(key=lambda x: x[1], reverse=True)

  for index, answer_stat in enumerate(answer_stat_list):
    if answer_stat[1] < index + 1:
      return index

  # If all answers have at least n upvotes where n is number of answers
  return len(answer_stat_list)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description = 'Compute your Q-Index')
  parser.add_argument('answer_dir', nargs='?', default='quora-answers',
                      help='The path of directory with all stored answers')
  parser.add_argument('-v', '--verbose', action='store_true',
                      help='Enable Verbose Messages')
  args = parser.parse_args()
  answer_stat_list = parse_all_answers(args.answer_dir, args.verbose)
  if args.verbose:
    print('A total of %d answers parsed.' % len(answer_stat_list))
  print('Your Q-Index is : %d' % compute_qindex(answer_stat_list))
