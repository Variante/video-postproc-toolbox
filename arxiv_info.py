import feedparser

def get_arxiv_title(arxiv_id):
    # Construct the URL for the arXiv API query
    url = f'http://export.arxiv.org/api/query?id_list={arxiv_id}'
    
    # Fetch the feed data from arXiv
    feed = feedparser.parse(url)
    
    # Check if the feed entries exist
    if feed.entries:
        # Extract the title of the first entry (paper)
        title = feed.entries[0].title
        
        # Clean up the title by removing newlines and extra spaces
        title = ' '.join(title.split())
        
        return title
    else:
        return None

if __name__ == '__main__':
    arxiv_id = '2404.07973'
    title = get_arxiv_title(arxiv_id)
    arxiv_link = f'https://arxiv.org/abs/{arxiv_id}'
    
    result = f"""{title}[{arxiv_id}]

论文题目：{title}
论文地址：{arxiv_link}

{title}\t{arxiv_link}"""
    
    print(result)
    with open('arxiv_info.txt', 'w', encoding='utf8') as f:
        f.write(result)
    
    