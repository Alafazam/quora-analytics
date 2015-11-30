# quora-analytics
Scripts to do some Quora analytics

This repo is under active development. I have directly copied the python crawler script from [Brian Bi's Quora Back Up](https://github.com/t3nsor/quora-backup).

`crawler.py` script should be executed first to fetch and save all your quora answers. Then each script can be executed as an independently.

#### Q-Index
The script named `qindex.py` computes the Q-Index of a user from his / her downloaded answers. Let's define a user's q-index, inspired by the h-index, as the highest number q for which it is true that the user has q answers with at least q upvotes. See [Q-Index Topic on Quora](https://www.quora.com/topic/Q-index-1) for more details.

#### View - UpVotes Statistics
The script named `view_upvote.py` computes multiple metrics related to views and upvotes of all your answers. The major metrics are :
- Total view across all answers
- Total upvotes across all answers
- Average views per answer
- Average upvotes per answer
- Average of (Views / Upvotes) per answers
- Ratio of total views across all answers and total upvotes across all answers
