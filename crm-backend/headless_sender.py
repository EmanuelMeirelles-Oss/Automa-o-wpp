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
    msg1 = f"Fala pessoal da {lead.nome}, tudo bom? Sou o Emanuel, desenvolvedor aqui de {lead.cidade} 👋"
    
    if lead.tem_site:
        msg2 = "Acompanho o trampo de voces e achei top! Vi o site atual, mas acredito que daria pra atrair muito mais clientes se passasse aquele nivel premium.\n\nAcesse aqui meu portfolio focado na area para voces sentirem o que quero dizer: https://portfolioemanueldev.vercel.app\n\nConseguimos trocar 5 minutinhos de ideia sem compromisso?"
    else:
        msg2 = "Acompanho o trampo de voces e achei top! Notei que ainda estao sem um site oficial pra profissionalizar os agendamentos.\n\nAcesse aqui o meu portfolio para ver na pratica o que quero dizer (vai carregar a previa do meu site direto no zap): https://portfolioemanueldev.vercel.app\n\nConseguimos trocar 5 minutinhos de ideia sem compromisso?"
    return msg1, msg2

# O Loop mestre rodara isolado numa thead conectada a sua Interface
def run_bot_worker():
    db = SessionLocal()
    
    # 1. Abre o WebDriver do Chrome (mantemos o diretorio cache para nao perder QRCode)
    chrome_options = Options()
    chrome_options.add_argument("user-data-dir=../.tmp/chrome_profile_pro")
    
    # IMPORTANTE: Desativando "Headless" por agora para fins de Scan de QR CODE, em producao ou 100% cloud, pode se usar headless. Como a diretiva eh "uso na propria maquina enquanto ve animes", manter a aba aberta ou invisivel eh uma escolha. Deixaremos em janela por precaucao do QR.
    chrome_options.add_experimental_option("detach", True) 

    service = Service(ChromeDriverManager().install())
    driver = None
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
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

            msg1, msg2 = gerar_mensagens_para_lead(lead)
            msg1_encoded = urllib.parse.quote(msg1)
            
            server.BOT_STATUS["logs"].append(f"Atacando -> {lead.nome} ({telefone})")
            
            try:
                driver.get(f"https://web.whatsapp.com/send?phone={telefone}&text={msg1_encoded}")
                
                # Aguarda responsividade de internet e loading Web WhatsApp
                wait_ticks = 15
                for _ in range(wait_ticks):
                    if not server.BOT_STATUS["is_running"]: break
                    time.sleep(1)
                
                if not server.BOT_STATUS["is_running"]: 
                    # Rollback caso cancele no meio do timer (para n perder)
                    lead.status_disparo = "PENDENTE"
                    db.commit()
                    break

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
