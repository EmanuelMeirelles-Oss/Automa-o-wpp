import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

# Paths - 3-Layer Architecture Setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
TMP_DIR = os.path.join(BASE_DIR, '.tmp')
SITE_DIR = os.path.join(BASE_DIR, 'site')

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(SITE_DIR, exist_ok=True)

# Logger Configuration
log_file = os.path.join(LOGS_DIR, 'automation.log')
logger = logging.getLogger('football_bot')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

fh = logging.FileHandler(log_file, encoding='utf-8')
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

def fetch_rss(url, limit=5):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        news_items = []
        
        for item in root.findall('./channel/item'):
            title = item.find('title').text if item.find('title') is not None else 'No Title'
            link = item.find('link').text if item.find('link') is not None else ''
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            # Formatar a data se houver (opcional) - O Google News tem data em formato padrão
            news_items.append({
                'title': title,
                'description': '', # Cleaning description to keep UI clean
                'url': link,
                'date': pubDate
            })
            
            if len(news_items) >= limit:
                break
                
        return news_items
    except Exception as e:
        logger.error(f"Erro ao buscar noticias do RSS: {e}")
        return []

def fetch_all_news():
    logger.info("Buscando as maiores notícias de futebol do Brasil e do Mundo...")
    
    # URL do Google News em Português
    url_world = "https://news.google.com/rss/search?q=futebol+internacional&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    url_brazil = "https://news.google.com/rss/search?q=futebol+brasileiro&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    world_news = fetch_rss(url_world, 5)
    brazil_news = fetch_rss(url_brazil, 5)
    
    logger.info(f"Encontradas {len(world_news)} notícias do mundo e {len(brazil_news)} do Brasil.")
    
    return {
        "world": world_news,
        "brazil": brazil_news
    }

def save_data_json(current_news):
    logger.info("Atualizando site/data.json...")
    data_path = os.path.join(SITE_DIR, 'data.json')
    
    # Structure setup
    data = {
        "current_world": [], 
        "current_brazil": [], 
        "history_world": [],
        "history_brazil": []
    }
    
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                # Keep old data if it has expected structure
                if "history_world" in old_data:
                    data = old_data
                elif "history" in old_data:
                    # Migration from old format
                    data["history_world"] = old_data.get("history", [])
        except Exception as e:
            logger.error(f"Erro ao ler data.json existente: {e}")
            
    fetch_date = datetime.now().strftime("%Y-%m-%d")
    
    # Move current world to history
    if data.get("current_world"):
        for item in data["current_world"]:
            item["fetch_date"] = fetch_date
            data["history_world"].insert(0, item)
            
    # Move current brazil to history
    if data.get("current_brazil"):
        for item in data["current_brazil"]:
            item["fetch_date"] = fetch_date
            data["history_brazil"].insert(0, item)
            
    # Set new current news
    data["current_world"] = current_news["world"]
    data["current_brazil"] = current_news["brazil"]
    
    # Limit history to ~50 elements
    data["history_world"] = data["history_world"][:50]
    data["history_brazil"] = data["history_brazil"][:50]
    
    try:
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"SUCESSO! Dados salvos em: {data_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar data.json: {e}")

def main():
    logger.info("---")
    logger.info("Iniciando bot de notícias de Futebol do Brasil e do Mundo...")
    all_news = fetch_all_news()
    
    if all_news["world"] or all_news["brazil"]:
        tmp_file = os.path.join(TMP_DIR, 'football_news.json')
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(all_news, f, indent=4, ensure_ascii=False)
        
        save_data_json(all_news)
        logger.info("PROCESSO CONCLUÍDO COM SUCESSO.")
    else:
        logger.error("Nenhuma notícia foi encontrada em ambos os feeds.")

if __name__ == '__main__':
    main()
