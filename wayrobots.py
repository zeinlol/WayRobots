import argparse
import re
import time

import requests

log = ""


def pprint(out):
    global log
    log += out + "\n"
    print(out)


def parse_robots(txt):
    txt = txt.split("\n")
    res = []
    for line in txt:
        if not "#" in line:
            if ":" in line and "/" in line and not "http" in line:
                res.append(line.split(":")[1].strip())
    return res


def fetch_content(ts, target):
    ts_dirs = []
    for timestap in ts:
        try:
            content = requests.get("http://web.archive.org/web/{}if_/{}".format(timestap, target)).content.decode(
                "utf-8")
            dirs = parse_robots(content)
            ts_dirs.append({timestap: dirs})
        except TypeError as e:
            print(e)
            pass
    return ts_dirs


def get_clear_links(host, list_links, search_word):
    links = re.findall(f".*?.{host[4:]}.*/{search_word}.txt", list_links)  # [4:] is for skipping http:// & https:// dif
    for link in links:
        if link.count('http') > 1:
            links[links.index(link)] = 'http' + link.split('http')[-1]
    return links


def wayback_find_robots(host):
    content = requests.get(
        "http://web.archive.org/cdx/m_search/cdx?url=*.{}/*&output=txt&fl=original&collapse=urlkey".format(
            host)).content.decode("utf-8")
    robots_files = get_clear_links(host, content, 'robots')
    contributors_files = get_clear_links(host, content, 'contributors')
    return set(robots_files), set(contributors_files)


def wayback_url(url, year):
    allowed_statuses = [200]
    try:
        result = requests.get(
            "http://web.archive.org/__wb/calendarcaptures?url={}&selected_year={}".format(url, year)).json()
    except:
        return

    for month in range(0, 12):

        m_search = result[month]
        weeks = len(m_search)
        current_day = 0

        for days in range(weeks):
            for day in m_search[days]:

                if day != None:
                    current_day += 1

                    if day != {}:
                        ts = day['ts']
                        st = day['st'][0]

                        if st in allowed_statuses:
                            timestamp2dir = fetch_content(ts, url)

                            for i in timestamp2dir:
                                for ts, val in i.items():
                                    yield ts, val


def check_endpoint_stat(endpoint):
    request = requests.head(endpoint)
    return request.status_code


def crawling_robots(endpoint):
    if '.' in endpoint:
        endpoint = endpoint.split('.')[0] + '\\.' + endpoint.split('.')[1]
    if '*' in endpoint:
        _tmp = [_temp.start() for _temp in re.finditer(r'\*', endpoint)]
        temp = endpoint[0:_tmp[0]]
        for i in range(len(_tmp)):
            if i in range(len(_tmp) - 1):
                temp = temp + "." + endpoint[_tmp[i]:_tmp[i + 1]]
            else:
                temp = temp + "." + endpoint[_tmp[i]:len(endpoint)]
                endpoint = ".*" + temp + ".*"
    else:
        endpoint = ".*" + endpoint + ".*"
    content = requests.get(f"http://web.archive.org/cdx/search/cdx?url={target}&matchType=prefix&from={year_from}&to={year_to}&output=txt&collapse=urlkey&fl=original", timeout=5000).content.decode("utf-8")
    try:
        files = re.findall(endpoint, content)
        return files
    except:
        exit(0)
    return files


parser = argparse.ArgumentParser(description='Welcome to domainker help page')
parser.add_argument('-i', '--input', type=str, help='Target host')
parser.add_argument('-o', '--output', type=str, help='Output file')
parser.add_argument('-y', '--year', type=str, help='Years Range e.g[2014-2019]')
args = parser.parse_args()

if not args.input:
    pprint("[ERROR] Please specify the target first using -i")
    exit()

if not args.year:
    pprint("[WARNING] You haven't specify the year, Using current year: %s" % time.strftime("%Y"))
    args.year = "%s-%s" % (time.strftime("%Y"), time.strftime("%Y"))

if not "-" in args.year:
    pprint("[ERROR] Please specify starting and ending year e.g[2014-2019]")
    exit()

year = args.year
target = args.input

robots_txt, contrib_txt = wayback_find_robots(target)

# if len(contrib_txt) == 0:
#     pprint("[contributors.txt] files not found!")
if len(contrib_txt) > 0:
    #     pprint(f"Found {len(contrib_txt)} contributors.txt on the following:")
    for url in contrib_txt:
        pprint(url)

if len(robots_txt) == 0:
    # pprint("[robots.txt] files not found!")
    exit(0)
else:
    #     pprint(f"Found {len(robots_txt)} robots.txt on the following:")
    for url in robots_txt:
        pprint(url)

year_from = int(year.split("-")[0])
year_to = int(year.split("-")[1])

for year in range(year_from, year_to + 1):
    for robot_file in robots_txt:

        wb = wayback_url(robot_file, year)

        _tmp = []
        for result in wb:
            for dir_name in result[1]:
                if dir_name not in _tmp:
                    # pprint("[%s]::[%s] Searching for [robots.txt] snapshot" % (year, robot_file))
                    # print("  |_-> " + dir_name)
                    if dir_name != "/":
                        for i in range(len(crawling_robots(dir_name))):
                            pprint(
                                f"{dir_name}||{crawling_robots(dir_name)[i]}||{check_endpoint_stat(crawling_robots(dir_name)[i])}")
                _tmp.append(dir_name)

if args.output:
    open(args.output, "w").write(log)
