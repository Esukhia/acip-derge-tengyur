import re
import requests
import yaml
from bs4 import BeautifulSoup
from pathlib import Path


def from_yaml(yml_path):
    return yaml.safe_load(yml_path.read_text(encoding="utf-8"))

def get_vol_id(page_ann):
    page_id = re.sub(">(.+?)<br>", "\g<1>", page_ann)
    vol_id = re.search("([a-zA-Z])\d+[a-zA-Z]", page_id).group(1)
    return vol_id


def bind_pages(pages, page_anns, text_vols):
    text = {}
    prev_vol_id = ""
    cur_vol_text = ""
    vol_walker = 0
    if re.search(">[a-zA-Z]\d+[a-zA-Z]<br>", page_anns[0]):
        prev_vol_id = get_vol_id(page_anns[0])
    for page_ann, page in zip(page_anns, pages):
        if prev_vol_id and prev_vol_id != get_vol_id(page_ann):
            text[text_vols[vol_walker]] = cur_vol_text
            cur_vol_text = f'{page.string}\n'
            vol_walker += 1
        else:
            cur_vol_text += f'{page.string}\n'
    if cur_vol_text:
        text[text_vols[vol_walker]] = cur_vol_text
    return text
    
        

def parse_text(text_id, text_vols):
    text = {}
    try:
        web_text = requests.get(f"https://www.istb.univie.ac.at/kanjur/rktsneu/etanjur/verif2.php?id={text_id}&coll=derge").text
    except:
        web_text = ""
    
    if web_text:
        soup = BeautifulSoup(web_text, features="html.parser")
        pages = soup.findAll("font", {"size" : "+2"})
        page_anns = re.findall("<hr>.+?<br>", web_text)
        if not page_anns:
            page_anns = re.findall("</table>.+?<br>", web_text)
        if pages:
            text = bind_pages(pages, page_anns, text_vols)
    return text

def get_text_vols(text_span):
    text_vols = []
    for span in text_span:
        text_vols.append(f"v{int(span['vol']):03}")
    return text_vols

def get_acip_text(text_id, text_span):
    text_vols = get_text_vols(text_span)
    text = parse_text(text_id, text_vols)
    return text

def get_completed_text_list():
    completed_text_ids = []
    text_paths  = list(Path('./acip_texts').iterdir())
    for text_path in text_paths:
        text_id = text_path.stem[:-5]
        completed_text_ids.append(text_id)
    return completed_text_ids


def scrap_derge_tengyur():
    completed_text_list = get_completed_text_list()
    derge_index = from_yaml(Path('./index.yml'))
    for uuid, text_info in derge_index['annotations'].items():
        text_id = text_info['work_id']
        if text_id in completed_text_list:
            continue
        acip_text = get_acip_text(text_id, text_info['span'])
        for vol_id, text in acip_text.items():
            Path(f'./acip_texts/{text_id}_{vol_id}.txt').write_text(text, encoding='utf-8')
        print(f"{text_id} completed...")


if __name__ == "__main__":
    scrap_derge_tengyur()