import csv
import urllib.parse
import os

LEADS_FILE = '.tmp/leads.csv'
OUTPUT_FILE = '.tmp/mensagens_geradas.csv'

# ROTEIROS OTIMIZADOS E MAIS CURTOS (HUMANIZADOS)
MSG1_QUEBRA_GELO = "Fala pessoal da {NOME_BARBEARIA}, tudo bom? Sou o Emanuel, desenvolvedor aqui de {CIDADE} 👋"

MSG2_SEM_SITE = """Acompanho o trampo de vocês e achei top! Notei que ainda estão sem um site oficial pra profissionalizar os agendamentos.\n\nAcesse aqui o meu portfólio para ver na prática o que quero dizer (o zap vai carregar a prévia do meu site aqui embaixo): https://portfolioemanueldev.vercel.app\n\nConseguimos trocar 5 minutinhos de ideia sem compromisso?"""

MSG2_COM_SITE = """Acompanho o trampo de vocês e achei top! Vi o site atual, mas acredito que daria pra atrair muito mais clientes se passasse aquele nível premium.\n\nAcesse aqui meu portfólio focado na área para vocês sentirem o que quero dizer: https://portfolioemanueldev.vercel.app\n\nConseguimos trocar 5 minutinhos de ideia sem compromisso?"""

def main():
    if not os.path.exists('.tmp'):
        os.makedirs('.tmp')

    if not os.path.exists(LEADS_FILE):
        print(f"Erro: Arquivo {LEADS_FILE} não encontrado.")
        return

    resultados = []

    try:
        with open(LEADS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if not all(k in reader.fieldnames for k in ['Nome', 'Telefone', 'Cidade', 'TemSite']):
                return

            for row in reader:
                nome = row.get('Nome', '').strip()
                cidade = row.get('Cidade', '').strip()
                tem_site = row.get('TemSite', '').strip().lower()
                
                telefone = row.get('Telefone', '').strip()
                for char in [' ', '-', '+', '(', ')']:
                    telefone = telefone.replace(char, '')

                msg1 = MSG1_QUEBRA_GELO.format(NOME_BARBEARIA=nome, CIDADE=cidade)

                if tem_site in ['não', 'nao', 'n', 'false', '0']:
                    msg2 = MSG2_SEM_SITE
                else:
                    msg2 = MSG2_COM_SITE
                
                # Gera link para a primeira MSG do Quebra-gelo apenas!
                link_wame = f"https://wa.me/{telefone}?text={urllib.parse.quote(msg1)}"
                
                resultados.append({
                    'Nome': nome,
                    'Telefone': telefone,
                    'Cidade': cidade,
                    'TemSite': row.get('TemSite', ''),
                    'Mensagem1': msg1,
                    'Mensagem2': msg2,
                    'Link_WhatsApp': link_wame
                })

    except Exception as e:
         return

    if resultados:
        fieldnames = ['Nome', 'Telefone', 'Cidade', 'TemSite', 'Mensagem1', 'Mensagem2', 'Link_WhatsApp']
        with open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in resultados:
                writer.writerow(r)
        
        print(f"SUCESSO! Foram geradas {len(resultados)} mensagens customizadas em duas etapas no arquivo '{OUTPUT_FILE}'.")

if __name__ == '__main__':
    main()
