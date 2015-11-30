def show_vu_stats(answer_stat_list, depth=10):
  '''
    This function computes the statistics related to views and upvotes and
    displays the top 'depth' performers
    Args:
      answer_stat_list : A list of list representing parsed answer statistics
      depth : It prints top 'depth' performers in answer_list.
  '''

  total_views = sum(zip(*answer_stat_list)[0])
  print('Total views = %d' % total_views)

  avg_views = float(total_views) / len(answer_stat_list)
  print('Average views on each answer = %.2f' % avg_views)

  depth = min(len(answer_stat_list), depth)

  if depth > 0:
    # Sort answers according to views in descending order
    answer_stat_list.sort(key=lambda x: x[0], reverse=True)
    print('Top %d most viewed answers are : ' % depth)
    for i in range(depth):
      print('%d. %s with %d views' % (i + 1, answer_stat_list[i][2],
                                      answer_stat_list[i][0])
      )

  total_upvotes = sum(zip(*answer_stat_list)[1])
  print('Total upvotes = %d' % total_upvotes)

  avg_upvotes = float(total_upvotes) / len(answer_stat_list)
  print('Average upvotes on each answer = %.2f' % avg_upvotes)

  if depth > 0:
    # Sort answers according to views in descending order
    answer_stat_list.sort(key=lambda x: x[1], reverse=True)
    print('Top %d most upvoted answers are : ' % depth)
    for i in range(depth):
      print('%d. %s with %d upvotes' % (i + 1, answer_stat_list[i][2],
                                      answer_stat_list[i][1])
      )

  total_vu_ratio = float(total_views) / total_upvotes
  print('Total Views / Total Upvotes = %.2f' % total_vu_ratio)

  total_of_vu_ratio = 0
  for i in range(len(answer_stat_list)):
    if answer_stat_list[i][1] == 0:
      ratio = 0
    else:
      ratio = float(answer_stat_list[i][0]) / answer_stat_list[i][1]
    answer_stat_list[i].append(ratio)
    total_of_vu_ratio += ratio
  avg_of_vu_ratio = float(total_of_vu_ratio) / len(answer_stat_list)
  print('Average of (Views / Upvotes) of each answer = %.2f' % avg_of_vu_ratio)

  vu_filtered_list = filter(lambda x: x[3] > 0, answer_stat_list)
  depth = min(depth, len(vu_filtered_list))

  if depth > 0:
    # Sort answers according to views in descending order
    vu_filtered_list.sort(key=lambda x: x[3])
    print('Top %d answers with minimum (Views / Upvotes Ratio Are) : ' % depth)
    for i in range(depth):
      print('%d. %s with (Views(%d)/ Upvotes(%d) = %.2f)' % (
            i + 1, vu_filtered_list[i][2], vu_filtered_list[i][0],
            vu_filtered_list[i][1], vu_filtered_list[i][3])
      )

if __name__ == "__main__":
  import argparse
  from parser import *

  parser = argparse.ArgumentParser(
    description = 'Computes Views and Upvote Statistics')
  parser.add_argument('answer_dir', nargs='?', default='quora-answers',
                      help='The path of directory with all stored answers')
  parser.add_argument('-v', '--verbose', action='store_true',
                      help='Enable Verbose Messages')
  parser.add_argument('-d', '-n', '--depth', nargs='?', default=10, type=int,
                      help='Control the number of top performers to display')
  args = parser.parse_args()
  answer_stat_list = parse_all_answers(args.answer_dir, args.verbose)
  if args.verbose:
    print('A total of %d answers parsed.' % len(answer_stat_list))
  show_vu_stats(answer_stat_list, args.depth)
