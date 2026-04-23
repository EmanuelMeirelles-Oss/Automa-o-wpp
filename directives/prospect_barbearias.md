# Diretiva de Prospecção Avançada: Barbearias (WhatsApp)

Esta diretiva define o processo, variáveis e roteiros para o disparo automatizado via WhatsApp com objetivo de agendar reuniões (Meet/Ligação) para venda de sites. A abordagem atual foca na dor de não ter site para agendamentos ou de ter um site que não passa o devido nível de profissionalismo do estabelecimento.

## 🎯 Objetivo
Agendar uma reunião de **15 minutos** sem compromisso para apresentar ideias e soluções (Foco é conversão por call, não venda via texto). 
**Produto Base**: Site Profissional para Barbearias por R$ 500,00 (responsivo, portfólio, botão de agendamento, domínio grátis por conta do desenvolvedor por 1 ano, 7 dias úteis).

---

## 📝 1. Estrutura de Variáveis

O robô de mensagens operará precisando das seguintes chaves (fornecidas via `.tmp/leads.csv`):
- `{{NOME_BARBEARIA}}` — Ex: Barbearia do João
- `{{CIDADE}}` — Ex: Florianópolis
- `{{TEM_SITE}}` — Marcador de Condição ("Sim" ou "Não").

---

## 💬 2. Roteiros Oficiais

### Variante A (Para barbearias SEM SITE)
Ativada quando a coluna *TemSite* = "Não".

> "Fala pessoal da {{NOME_BARBEARIA}}, tudo bom? Sou o Emanuel, desenvolvedor daqui de {{CIDADE}}. 
> Vi o perfil de vocês e notei que ainda não têm um site pra facilitar os agendamentos. Crio estruturas exatamente pra isso (olha meu trabalho: portfolioemanueldev.vercel.app). 
> Teria 15 minutinhos essa semana pra trocarmos uma ideia por ligação ou Meet?"

### Variante B (Para barbearias COM SITE FRACO)
Ativada quando a coluna *TemSite* = "Sim".

> "Fala pessoal da {{NOME_BARBEARIA}}, tudo bom? Sou o Emanuel, desenvolvedor daqui de {{CIDADE}}. 
> Achei o trampo de vocês top, mas vi o site atual e acredito que dê pra passar um profissionalismo muito maior nele. Eu sou especialista em barbearias (portfolioemanueldev.vercel.app). 
> Conseguimos trocar 15 minutos de ideia sem compromisso, por Meet ou ligação, pra eu mostrar uma visão?"

---

## ⚙️ 3. Pipeline de Execução (Modus Operandi)

1. **População de Dados**: Você deve colar as informações das leads provindas do Google Maps dentro do arquivo base `.tmp/leads.csv`. A primeira linha deve, OBRIGATORIAMENTE, ser o cabeçalho: `Nome,Telefone,Cidade,TemSite`.
2. **Geração de URLs**: Execute via terminal o script gerador: 
   ```bash
   python execution/generate_messages.py
   ```
3. **Resultado / Disparo**: O arquivo `.tmp/mensagens_geradas.csv` será gerado automaticamente contendo suas mensagens preenchidas e a URL Final com a codificação do Whatsapp `https://wa.me/...&text=...` perfeita para disparos.

## 🚀 4. Próximos Passos (Backlog)
- [ ] Construir/Integrar Robô de Disparo Automático para ler o `.tmp/mensagens_geradas.csv` e despachar de forma humanizada (delay configurado das APIs oficiais ou via Baileys/N8N para simulação real de uso sem risco de BAN).
- [ ] Opcional: Script para coleta via Google Maps Search Tool (Google Places) que jogue os dados direto no CSV evitando copia e cola.
