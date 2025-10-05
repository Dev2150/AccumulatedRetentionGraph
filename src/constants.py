from anki import stats

# Card State Categories & Colors
CAT_LEARNING = 0
CAT_YOUNG = 1
CAT_MATURE = 2
CAT_RETAINED = 3

COLOR_LEARNING = stats.colLearn
COLOR_YOUNG = stats.colYoung
COLOR_MATURE = stats.colMature
COLOR_RETAINED = "#004080" # Dark blue, adjust as needed

# Interval thresholds (in days)
INTERVAL_LEARNING_MAX = 7
INTERVAL_YOUNG_MAX = 21
INTERVAL_MATURE_MAX = 84