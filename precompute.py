import json
import zlib
import time
from concurrent.futures import ThreadPoolExecutor
from typing import *

# data is global in the .js

# Implement resolveLink
def resolveLink(data, link):
    """
    Get the link for the article by resolving the redirects
    """
    if data.get(link) is None:
        return link
    if data[link].get('redirect') and data[link]['redirect'] != link:
        return resolveLink(data, data[link]['redirect'])
    return link

# Implement computeCommonLinks
def computeCommonLinks(data, a, b):
    # Resolve the links
    a = resolveLink(data, a)
    b = resolveLink(data, b)
    # Get the resolved links for every single article on a and b
    aLinks = set(map(lambda x: resolveLink(data, x), data[a].get('links', [])))
    bLinks = set(map(lambda x: resolveLink(data, x), data[b].get('links', [])))
    for article in data:
        article_links = data[article].get('links', [])
        if not article_links:
            continue
        article_links = set(map(lambda x: resolveLink(data, x), article_links))
        # For each article, if a is in the links, add the article to aLinks
        if a in article_links:
            aLinks.add(article)
        if b in article_links:
            bLinks.add(article)
    # Return the length of the intersection of aLinks and bLinks
    return len(aLinks.intersection(bLinks))

# Implement computeDistance
def computeDistance(data, a, b):
    a = resolveLink(data, a)
    b = resolveLink(data, b)
    if a == b:
        return 0
    distances = {}
    distances[a] = 0
    # BFS for the shortest path to b
    queue = [a]
    while True:
        if len(queue) == 0:
            break
        article = queue.pop(0)
        # If the article does not exist or has no links, skip
        if article not in data or not data[article].get('links', []):
            continue
        # Else resolve all links and add them to the queue
        links = list(map(lambda x: resolveLink(data, x), data[article].get('links', [])))
        for link in links:
            if link in distances:
                continue
            distances[link] = distances[article] + 1
            # If we have reached the target, break
            if link == b:
                break
            queue.append(link)
    return distances[b] if b in distances else None

# Implement random
def random(n):
    current_time = time.gmtime(time.time())
    year = current_time.tm_year
    month = current_time.tm_mon
    day = current_time.tm_mday
    from ctypes import c_int32
    hash_value = day + month * 31 + year * 31 * 12
    hash_value = c_int32(hash_value).value
    hash_value ^= c_int32(hash_value << 13).value
    hash_value ^= c_int32(hash_value >> 7).value
    hash_value ^= c_int32(hash_value << 17).value
    return year, month, day, c_int32(hash_value).value % n

# Load data and return relevant values
def load_data():
    filtered_articles = []
    article_map = {}
    with open("data.bin", 'rb') as file:
        compressed_data = file.read()
    decompressed_data = zlib.decompress(compressed_data)
    data: dict = json.loads(decompressed_data.decode('utf-8'))

    for article in data.keys():
        entry: dict = data[article]
        links = entry.get('links')
        if links is None:
            continue
        for link in links:
            link = resolveLink(data, link)
            article_map[link] = article_map.get(link, 0) + 1
    
    filtered_articles = [art for art in data if data[art].get('links') is not None and article_map.get(art, 0) >= 64]
    filtered_articles.sort()
    y, m, d, idx = random(len(filtered_articles))
    target = filtered_articles[idx]
    links = article_map[target]
    difficulty = ''
    if links >= 512:
        difficulty = 'easy'
    elif links >= 256:
        difficulty = 'medium'
    elif links >= 128:
        difficulty = 'hard'
    else:
        difficulty = 'impossible'

    return data, filtered_articles, difficulty, target, links, y, m, d

def precompute(raw_data: dict, filtered: list[str], target: str):
    # Essentially we want to precompute the common links and the distance between every pair of articles
    # We will store this in a dictionary
    # The dictionary will be stored as a binary file
    # We do this via a BFS traversal of the graph with the starting point as the target
    start = resolveLink(raw_data, target)
    data = {}
    # Dict contains a tuple of (avg_distance,, commonlinks, occurrences)
    data[start] = (0, 0, 0)

    def helper(article):
        dists = [x for x in [computeDistance(raw_data, start, article), computeDistance(raw_data, article, start)] if x is not None]
        avg_distance = "∞" if len(dists) == 0 else sum(dists) / len(dists)
        occurrences = raw_data[target].get('content', '').count(article)
        common_links = computeCommonLinks(raw_data, start, article)
        return (avg_distance, common_links, occurrences), article

    print("Precomputing data...")
    from tqdm import tqdm
    with ThreadPoolExecutor(max_workers = 8) as executor:
        futures = []
        for article in tqdm(filtered):
            if article == start:
                continue
            article_link = resolveLink(raw_data, article)
            # We compute the distance from start to article and article to start
            futures.append(executor.submit(helper, article_link))
        for future in tqdm(futures, total=len(futures)):
            ans, article = future.result()
            data[article] = ans
    return data

# calculate runtime
start = time.time()
raw_data, filtered, difficulty, target, links, y, m, d = load_data()
computed_data = precompute(raw_data, filtered, target)
article_data = {
    'difficulty': difficulty,
    'target': target,
    'data': computed_data,
    'filtered': filtered,
    'links': links
}
time_data = {
    'year': y,
    'month': m,
    'day': d
}
with open("./public/pre_data.bin", 'wb') as file:
    file.write(zlib.compress(json.dumps(article_data).encode('utf-8')))
with open("./public/pre_time.bin", 'wb') as file:
    file.write(zlib.compress(json.dumps(time_data).encode('utf-8')))
end = time.time()
print(f"Time taken: {end - start} seconds")