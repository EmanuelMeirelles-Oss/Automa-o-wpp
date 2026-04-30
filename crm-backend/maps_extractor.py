import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from database import SessionLocal, Lead
import server

def run_maps_extraction(query: str):
    server.BOT_STATUS["logs"].append(f"🔎 Iniciando Radar Maps para: '{query}'")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Roda invisível para não atrapalhar
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        server.BOT_STATUS["logs"].append(f"❌ Erro ao abrir Chrome invisível: {e}")
        return

    db = SessionLocal()
    
    try:
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        driver.get(url)
        time.sleep(5)
        
        # No Google Maps novo, os links dos lugares costumam ter a classe 'hfpxzc'
        places = driver.find_elements(By.XPATH, "//a[contains(@href, 'https://www.google.com/maps/place/')]")
        
        # Scroll para carregar mais resultados na barra lateral
        server.BOT_STATUS["logs"].append("Descendo a lista para carregar mais empresas...")
        for _ in range(4):
            temp_places = driver.find_elements(By.XPATH, "//a[contains(@href, 'https://www.google.com/maps/place/')]")
            if temp_places:
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", temp_places[-1])
                    time.sleep(2)
                except:
                    pass
        
        places = driver.find_elements(By.XPATH, "//a[contains(@href, 'https://www.google.com/maps/place/')]")

        if not places:
            server.BOT_STATUS["logs"].append("⚠️ Nenhum resultado claro encontrado. O Google pode estar bloqueando a visão.")
            return

        server.BOT_STATUS["logs"].append(f"📍 Encontrados {len(places)} locais na página. Analisando e filtrando...")
        added_count = 0
        
        # Limita a 30 nesta versão para rodar em um tempo aceitável
        for i in range(min(len(places), 30)):
            if not server.BOT_STATUS["is_extracting"]: break
            try:
                clicked = False
                # Recarrega a lista para evitar o erro de 'Stale Element'
                current_places = driver.find_elements(By.XPATH, "//a[contains(@href, 'https://www.google.com/maps/place/')]")
                if i >= len(current_places): break
                
                place = current_places[i]
                nome = place.get_attribute("aria-label")
                if not nome: continue
                
                # Clica no local para abrir a barra lateral com os detalhes
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", place)
                time.sleep(1)
                place.click()
                clicked = True
                time.sleep(3) # Espera a aba lateral carregar os dados
                
                # Checa se existe site (data-item-id contem authority)
                site_btns = driver.find_elements(By.XPATH, "//a[contains(@data-item-id, 'authority')]")
                tem_site = True if site_btns else False
                
                import re
                
                # Extraindo Avaliação do aria-label
                avaliacao = "Sem avaliação"
                match_estrelas = re.search(r'(\d+[,.]\d+)\s+estrelas?', nome.lower())
                if match_estrelas:
                    avaliacao = f"{match_estrelas.group(1)}⭐"
                elif "estrelas" in nome.lower() or "avaliações" in nome.lower():
                    pass 
                
                # REGRA DE NEGÓCIO: Ignorar quem JÁ TEM SITE
                if tem_site:
                    server.BOT_STATUS["logs"].append(f"Ignorado: {nome[:15]}... (Já possui site)")
                    if clicked:
                        driver.back()
                        time.sleep(2)
                    continue

                # Tenta achar o botão de telefone
                phone_btns = driver.find_elements(By.XPATH, "//button[contains(@data-item-id, 'phone:tel:')]")
                telefone = ""
                if phone_btns:
                    telefone = phone_btns[0].get_attribute("data-item-id").replace("phone:tel:", "")
                
                if not telefone:
                    server.BOT_STATUS["logs"].append(f"Ignorado: {nome[:15]}... (Sem telefone)")
                    if clicked:
                        driver.back()
                        time.sleep(2)
                    continue
                    
                # Extrai Instagram
                insta_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'instagram.com')]")
                instagram = insta_links[0].get_attribute("href") if insta_links else None
                    
                cidade = query.split()[-1] 
                
                # Salva no Banco de Dados
                existing = db.query(Lead).filter(Lead.telefone == telefone).first()
                if not existing:
                    new_lead = Lead(nome=nome, telefone=telefone, cidade=cidade, tem_site=tem_site, instagram=instagram, avaliacao=avaliacao, status_disparo="PENDENTE")
                    db.add(new_lead)
                    db.commit()
                    added_count += 1
                    
                    ig_tag = "(Tem Instagram)" if instagram else "(Sem Insta)"
                    server.BOT_STATUS["logs"].append(f"🎯 Capturado ALVO IDEAL: {nome[:20]}... | {avaliacao} {ig_tag}")
                else:
                    server.BOT_STATUS["logs"].append(f"Ignorado: {nome[:15]}... (Já existe no banco)")
                
                # IMPORTANTE: Sempre voltar para a lista de resultados!
                if clicked:
                    driver.back()
                    time.sleep(2)
                
            except Exception as e:
                # Se falhar um, tenta voltar e vai pro próximo
                try:
                    if clicked:
                        driver.back()
                        time.sleep(2)
                except:
                    pass
                continue
                
        server.BOT_STATUS["logs"].append(f"🏁 Extração finalizada! {added_count} novos leads adicionados.")

    except Exception as e:
        server.BOT_STATUS["logs"].append(f"❌ Erro fatal no extrator: {e}")
    finally:
        server.BOT_STATUS["is_extracting"] = False
        driver.quit()
        db.close()
