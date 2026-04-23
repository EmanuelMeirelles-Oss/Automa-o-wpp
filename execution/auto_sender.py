import csv
import time
import os
import sys
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    sys.exit(1)

MESSAGES_FILE = '.tmp/mensagens_geradas.csv'

def send_whatsapp_messages():
    print("="*50)
    print("INICIANDO ROBO DE DISPARO FRACIONADO E HUMANO DO WHATSAPP")
    print("="*50)
    
    if not os.path.exists(MESSAGES_FILE):
        return

    leads = []
    with open(MESSAGES_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
    
    if not leads: return

    chrome_options = Options()
    user_data_dir = os.path.join(os.getcwd(), '.tmp', 'chrome_profile')
    chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    chrome_options.add_experimental_option("detach", True) 

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.get("https://web.whatsapp.com/")
    print("\nESPERA DE 20 SEGUNDOS! Se precisar escanear QR Code do seu Whatsapp, faca isso.")
    time.sleep(20) 

    enviados_com_sucesso = 0

    for index, lead in enumerate(leads, start=1):
        nome = lead.get("Nome", "Local")
        telefone = lead.get("Telefone", "").replace("+", "").replace(" ", "").replace("-", "").strip()
        
        if len(telefone) in [10, 11] and not telefone.startswith("55"):
            telefone = "55" + telefone

        mensagem1 = lead.get("Mensagem1", "")
        mensagem2 = lead.get("Mensagem2", "")

        msg1_encoded = urllib.parse.quote(mensagem1)
        
        print(f"[{index}/{len(leads)}] Processando Lead: {nome}...")
        
        try:
            # 1. Carrega o navegador diretamente na MSG1 (Quebra gelo)
            direct_web_link = f"https://web.whatsapp.com/send?phone={telefone}&text={msg1_encoded}"
            driver.get(direct_web_link)
            
            print("Carregando o chat para envio da Mensagem 1...")
            time.sleep(15) 

            # Tenta Disparar a Primeira Msg
            botoes = driver.find_elements(By.XPATH, '//span[@data-icon="send"]')
            if botoes:
                botoes[0].click()
            else:
                webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
            
            print("Mensagem 1 inicial enviada (Aguardando resposta humana simulada de 5 segundos)!")
            time.sleep(5)
            
            # 2. Agora Digita a MSG2 que contém o Link para ele gerar a imagem la no zap na hora!
            # Vamos quebrar as quebras de linha da msg2 para o send_keys enviar certinho
            linhas_msg2 = mensagem2.split('\n')
            Action = webdriver.ActionChains(driver)
            for i, linha in enumerate(linhas_msg2):
                Action.send_keys(linha)
                if i < len(linhas_msg2) - 1:
                    # SHIFT+ENTER = quebra a linha dentro do input sem enviar ainda
                    Action.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
            
            Action.perform() # Escreve tudo
            print("Pausando 4 segundos antes de enviar para permitir o Whatsapp carregar a Imagem da Vercel...")
            time.sleep(4)
            # Envia efetivamente
            webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()

            enviados_com_sucesso += 1
            print(f"Mensagem 2 enviada com Link/Imagem para {nome}!")
            print("Pausando 15s antes do proximo lead para seguranca anti-ban...")
            time.sleep(15)

        except Exception as e:
            print(f"Erro ao disparar para {nome}: {e}")

    print("\n" + "="*50)
    print(f"FINALIZADO! Disparos Duplos bem sucedidos: {enviados_com_sucesso}/{len(leads)}")
    print("="*50)
    
if __name__ == '__main__':
    send_whatsapp_messages()
