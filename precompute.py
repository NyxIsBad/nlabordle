import json
import zlib
import time
from tqdm import tqdm
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
def computeCommonLinks(data, a, b, aLinks):
    # Resolve the links
    a = resolveLink(data, a)
    b = resolveLink(data, b)
    # Get the resolved links for every single article on a and b
    aLinks = set(map(lambda x: resolveLink(data, x), data[a].links))
    bLinks = set(map(lambda x: resolveLink(data, x), data[b].links))
    for article in data:
        # For each article, if a is in the links, add the article to aLinks
        if data[article].links and resolveLink(data, a) in data[article].links:
            aLinks.add(article)
        if data[article].links and resolveLink(data, b) in data[article].links:
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
        article = queue.pop(0)
        # If we have gone through all the articles
        if not article:
            break
        # If the article does not exist or has no links, skip
        if not data[article] or not data[article].links:
            continue
        # Else resolve all links and add them to the queue
        links = list(map(lambda x: resolveLink(data, x), data[article].links))
        for link in links:
            if link in distances:
                continue
            distances[link] = distances[article] + 1
            # If we have reached the target, break
            if link == b:
                break
            queue.append(link)
    return distances[b]

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
    return c_int32(hash_value).value % n

# Load data and return relevant values
def load_data():
    filtered_articles = []
    article_map = {}
    with open("data.bin", 'rb') as file:
        compressed_data = file.read()
    decompressed_data = zlib.decompress(compressed_data)
    data: dict = json.loads(decompressed_data.decode('utf-8'))

    for article in tqdm(data.keys(), desc="Processing articles"):
        entry: dict = data[article]
        links = entry.get('links')
        if links is None:
            continue
        for link in links:
            link = resolveLink(data, link)
            article_map[link] = article_map.get(link, 0) + 1
    
    filtered_articles = [art for art in data if data[art].get('links') is not None and article_map.get(art, 0) >= 64]
    filtered_articles.sort()
    target = filtered_articles[random(len(filtered_articles))]
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

    return data, filtered_articles, difficulty, target

def precompute(raw_data: dict, target: str):
    # Essentially we want to precompute the common links and the distance between every pair of articles
    # We will store this in a dictionary
    # The dictionary will be stored as a binary file
    # We do this via a BFS traversal of the graph with the starting point as the target
    start = resolveLink(raw_data, target)
    start_links = set(map(lambda x: resolveLink(raw_data, x), raw_data[start].get('links', [])))
    for x in raw_data:
        if raw_data[x].get('links') and start in raw_data[x]['links']:
            start_links.add(x)
    data = {}
    # Dict contains a tuple of (common links, distance)
    data[start] = (0, 0)
    queue = [start]
    print(len(raw_data))
    with tqdm(total=len(raw_data), desc="Precomputing") as pbar:
        while True:
            if len(queue) == 0:
                break
            article = queue.pop(0)
            # If the article does not exist or has no links, skip
            if not raw_data[article] or not raw_data[article].get('links'):
                continue
            # Else resolve all links and add them to the queue
            links = list(map(lambda x: resolveLink(raw_data, x), raw_data[article].get('links', [])))
            # For each link, compute the common links and distance
            for link in links:
                if not link in raw_data or link in data:
                    continue
                # print(f"Computing {article} -> {link}")
                link = resolveLink(raw_data, link)
                if link in data:
                    continue
                link_links = set(map(lambda x: resolveLink(raw_data, x), raw_data[link].get('links', [])))
                for x in raw_data:
                    if raw_data[x].get('links') and link in raw_data[x]['links']:
                        link_links.add(x)
                common_links = len(start_links.intersection(link_links))
                data[link] = (common_links, data[article][1] + 1)
                queue.append(link)
            pbar.update(1)
    with open("precomputed.bin", 'wb') as file:
        compressed_data = zlib.compress(json.dumps(data).encode('utf-8'))
        file.write(compressed_data)
    # for debugging purposes
    with open("precomputed.json", 'w') as file:
        file.write(json.dumps(data))
    return data

# calculate runtime
start = time.time()
raw_data, filtered, difficulty, target = load_data()
computed_data = precompute(raw_data, target)
end = time.time()
print(f"Time taken: {end - start} seconds")