second_array = [60.0, 60.0, 24.0, 365.0 / 7.0 / 12.0, 12.0]
locale = [
    ["just now",       "a while"],
    ["{} seconds ago", "in {} seconds"],
    ["1 minute ago",   "in 1 minute"],
    ["{} minutes ago", "in {} minutes"],
    ["1 hour ago",     "in 1 hour"],
    ["{} hours ago",   "in {} hours"],
    ["1 day ago",      "in 1 day"],
    ["{} days ago",    "in {} days"],
    ["1 week ago",     "in 1 week"],
    ["{} weeks ago",   "in {} weeks"],
    ["1 month ago",    "in 1 month"],
    ["{} months ago",  "in {} months"],
    ["1 year ago",     "in 1 year"],
    ["{} years ago",   "in {} years"],
]

def time_diff(before, after):
    diff_seconds = (before - after).total_seconds()
    ago_in = 0
    if diff_seconds < 0:
        ago_in = 1
        diff_seconds *= -1
    tmp = 0
    i = 0
    while i < len(second_array):
        tmp = second_array[i]
        if diff_seconds >= tmp:
            i += 1
            diff_seconds /= tmp
        else:
            break
    diff_seconds = int(diff_seconds)
    i *= 2
    if diff_seconds > (i == 0 and 9 or 1):
        i += 1
    tmp = locale[i][ago_in]
    if '{}' in tmp:
        return tmp.format(diff_seconds)
    return tmp
    