import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from database import SessionLocal, Lead
import server

# Funcao pra gerar as copys do lead
def gerar_mensagens_para_lead(lead):
    msg1 = (
        f"Opa, pessoal da {lead.nome}! Tudo bem? "
        f"Aqui é o Emanuel, desenvolvedor de sites aqui de {lead.cidade} mesmo 👋\n\n"
        f"Tava dando uma olhada no trabalho de vocês hoje — ficou uma pergunta na minha cabeça que queria compartilhar com vocês."
    )

    if lead.tem_site:
        msg2 = (
            f"O trabalho de vocês é visivelmente bom — mas o site atual não tá comunicando isso da forma que merecia.\n\n"
            f"Tenho uma ideia específica pra {lead.nome} que já apliquei em outros estabelecimentos aqui da região. "
            f"Dá uma olhada rápida no que eu faço: https://portfolioemanueldev.vercel.app"
        )
    else:
        msg2 = (
            f"Percebi que vocês ainda não têm um site — e isso tá custando cliente todo dia, "
            f"porque quem procura barbearia no Google simplesmente não acha vocês.\n\n"
            f"Tenho uma solução específica pra {lead.nome} que já apliquei aqui na região. "
            f"Dá uma olhada rápida: https://portfolioemanueldev.vercel.app"
        )

    msg3 = (
        f"Teriam uns 5 minutinhos essa semana pra eu mostrar como ficaria pra vocês especificamente? "
        f"Sem compromisso — se não fizer sentido, tudo bem também 👊"
    )

    return msg1, msg2, msg3

# O Loop mestre rodara isolado numa thead conectada a sua Interface
def run_bot_worker():
    db = SessionLocal()
    
    # 1. Abre o WebDriver do Chrome (mantemos o diretorio cache para nao perder QRCode)
    chrome_options = Options()
    
    import os
    profile_path = os.path.abspath(os.path.join(os.getcwd(), "..", ".tmp", "wpp_profile"))
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
        
    chrome_options.add_argument(f"user-data-dir={profile_path}")
    
    # IMPORTANTE: Desativando "Headless" por agora para fins de Scan de QR CODE.
    chrome_options.add_experimental_option("detach", True) 

    driver = None
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://web.whatsapp.com/")
        server.BOT_STATUS["logs"].append("Aguardando Whatsapp Web sincronizar (20 seg)...")
        time.sleep(20)
        
        server.BOT_STATUS["logs"].append("Sistema de Escala Iniciado! Procurando leads pendientes...")

        # O Loop diario fica vivo ate o painel enviar ordem de parada
        while server.BOT_STATUS["is_running"]:
            
            # Pega o primeiro lead q estao sobrando na base PENDENTE
            lead = db.query(Lead).filter(Lead.status_disparo == "PENDENTE").first()
            
            if not lead:
                server.BOT_STATUS["logs"].append("Todos os Leads atuais foram atingidos! Em breve procure carregar mais do extrator Mapsearch.")
                server.BOT_STATUS["is_running"] = False
                break
                
            lead.status_disparo = "ENVIANDO"
            db.commit()
            
            telefone = str(lead.telefone).replace("+", "").replace(" ", "").replace("-", "").strip()
            if len(telefone) in [10, 11] and not telefone.startswith("55"):
                telefone = "55" + telefone

            msg1, msg2, msg3 = gerar_mensagens_para_lead(lead)
            msg1_encoded = urllib.parse.quote(msg1)
            
            server.BOT_STATUS["logs"].append(f"Atacando -> {lead.nome} ({telefone})")
            
            try:
                driver.get(f"https://web.whatsapp.com/send?phone={telefone}&text={msg1_encoded}")
                
                # Aguarda responsividade de internet e loading Web WhatsApp
                wait_ticks = 20
                send_button_found = False
                invalid_number = False
                
                for _ in range(wait_ticks):
                    if not server.BOT_STATUS["is_running"]: break
                    
                    # Verifica se o botao de enviar ja carregou (sinal verde)
                    if driver.find_elements(By.XPATH, '//span[@data-icon="send"]'):
                        send_button_found = True
                        break
                        
                    # Verifica se deu erro de numero invalido
                    page_text = driver.page_source.lower()
                    if "url é inválido" in page_text or "url is invalid" in page_text or "não existe" in page_text:
                        invalid_number = True
                        break
                        
                    time.sleep(1)
                
                if not server.BOT_STATUS["is_running"]: 
                    # Rollback caso cancele no meio do timer (para n perder)
                    lead.status_disparo = "PENDENTE"
                    db.commit()
                    break

                if invalid_number:
                    lead.status_disparo = "ERRO"
                    db.commit()
                    server.BOT_STATUS["logs"].append(f"⚠️ Alerta: O número de {lead.nome} NÃO tem WhatsApp! Pulando...")
                    continue
                    
                if not send_button_found:
                    lead.status_disparo = "ERRO"
                    db.commit()
                    server.BOT_STATUS["logs"].append(f"⚠️ Alerta: Internet lenta ou falha ao carregar o chat de {lead.nome}. Pulando...")
                    continue

                # Dispara M1
                botoes = driver.find_elements(By.XPATH, '//span[@data-icon="send"]')
                if botoes: botoes[0].click()
                else: webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
                
                time.sleep(4)
                
                # Inputa e Dispara M2 fracionada
                linhas_msg2 = msg2.split('\n')
                Action = webdriver.ActionChains(driver)
                for i, linha in enumerate(linhas_msg2):
                    Action.send_keys(linha)
                    if i < len(linhas_msg2) - 1:
                        Action.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
                
                Action.perform()
                time.sleep(3) # Carga pro Whatsapp construir Thumbnail Vercel
                webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
                
                time.sleep(4)
                
                # Inputa e Dispara M3
                linhas_msg3 = msg3.split('\n')
                Action3 = webdriver.ActionChains(driver)
                for i, linha in enumerate(linhas_msg3):
                    Action3.send_keys(linha)
                    if i < len(linhas_msg3) - 1:
                        Action3.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
                        
                Action3.perform()
                time.sleep(1)
                webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()

                lead.status_disparo = "SUCESSO"
                db.commit()
                server.BOT_STATUS["logs"].append(f"Lead validada e abordada: {lead.nome}.")
                
                # ANTIBAN (Pausa massiva p/ humanos - descansa de 3 a 5 minutos na versao de escala 500/dia)
                # Para ele ver que ta funcionando logo agora, um teste rapido de 30seg. Mas pro futuro mude para 180 a 300 segundos
                descanco = 30
                server.BOT_STATUS["logs"].append(f"Descansando bot por segurança antes da proxima meta...({descanco}s)")
                
                # Parada responsiva a botao
                for _ in range(descanco):
                    if not server.BOT_STATUS["is_running"]: break
                    time.sleep(1)

            except Exception as ev_internal:
                lead.status_disparo = "ERRO"
                lead.log_erro = str(ev_internal)
                db.commit()
                server.BOT_STATUS["logs"].append(f"Alerta: Algo bloqueou o envio para {lead.nome} ({ev_internal})")

    except Exception as e:
        server.BOT_STATUS["logs"].append(f"Erro Fatal no Driver: {e}")
        server.BOT_STATUS["is_running"] = False
    
    finally:
        if driver:
            try: driver.quit()
            except: pass
        db.close()
        server.BOT_STATUS["logs"].append("Processo em Background finalizado de forma completamente segura.")
