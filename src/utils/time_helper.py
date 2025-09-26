import datetime


def parse_time(time_str):
    if time_str is None:
        return None
    try:
        return datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.datetime.strptime(time_str, '%Y-%m-%d')
        except ValueError:
            return datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')


def parse_str_to_time(time_str):
    if time_str is None:
        return None
    if not time_str.endswith(' OO:OO:OO') and len(time_str) <= 10:
        time_str = time_str + ' 00:00:00'
    return datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
