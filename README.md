# EmailTriageAI

Aplicacao web para triagem de emails corporativos com NLP, baseline classico e LLM. O foco e reduzir ruido, gerar respostas sugeridas e permitir feedback rapido sem banco de dados.

## Stack
- FastAPI + Jinja2
- Gemini (resposta em JSON validada com Pydantic)
- NLP com NLTK (stopwords + RSLPStemmer)
- Baseline ML: TF-IDF + LogisticRegression
- Frontend leve com HTML/CSS/JS

## Funcionalidades
- Upload de email (.txt/.pdf) ou texto colado
- Pre-processamento NLP (limpeza, stopwords, stemming)
- Classificacao Produtivo/Improdutivo
- Resposta sugerida em PT-BR
- Tags, resumo e confianca
- Historico local (ultima 5 analises)
- Feedback com armazenamento em CSV

## Como funciona
1. Entrada por upload (.txt/.pdf) ou texto colado
2. Pre-processamento com NLTK (stopwords + stemming)
3. Baseline TF-IDF + LogisticRegression define a categoria quando confiante
4. Gemini gera classificacao, resumo, tags e resposta sugerida em JSON
5. Pydantic valida formato e limites de tamanho

## Dados e treinamento
- Dataset de exemplo em `data/emails_seed.csv`
- Exemplos prontos em `examples/`
- Treine o baseline com `scripts/train_baseline.py`
- Nao ha fine-tuning do LLM; a melhoria vem do prompt e do baseline supervisionado

## Como rodar local
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Acesse: http://localhost:8000

## Variaveis de ambiente
Crie um arquivo `.env` baseado no `.env.example`:
- `GEMINI_API_KEY`: chave da API do Gemini
- `GEMINI_MODEL`: modelo (ex.: gemini-2.5-flash)
- `LOG_LEVEL`: nivel do log
- `ENVIRONMENT`: development ou production
- `SESSION_SECRET`: segredo para cookies de sessao/CSRF
- `ALLOWED_HOSTS`: allowlist de hosts separados por virgula
- `CORS_ALLOW_ORIGINS`: origens permitidas (opcional)
- `FORCE_HTTPS`: redireciona HTTP para HTTPS quando true
- `ENABLE_HSTS`: adiciona HSTS quando true (ou em production)

## Treinar baseline
```bash
python scripts/train_baseline.py
```
Os artefatos ficam em `models/baseline.joblib`.

## Deploy no Render
- Suba o repo no GitHub
- Crie um novo Web Service no Render
- Conecte o repo e mantenha as configuracoes padrao do `render.yaml`
- Configure as variaveis no painel (GEMINI_API_KEY)

Comandos:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Testes
```bash
pytest
```

## Seguranca (resumo)
- Headers de seguranca com CSP, X-Frame-Options, nosniff e Referrer-Policy.
- CSRF obrigatorio em todos os POSTs (form + header).
- Upload seguro (tamanho, magic bytes, extensoes, limite de paginas PDF).
- Rate limit por IP e limite de body para reduzir DoS.
- Timeouts para leitura de PDF e chamada ao LLM.
- Prompt injection mitigado com regras no prompt + sinais de risco.

## Threat model (OWASP)
- OWASP Top 10 + OWASP API Top 10: validacao de entrada, headers, CORS e rate limit.
- File upload: bloqueio de extensoes suspeitas e validacao de magic bytes.
- XSS/CSRF: CSP forte, autoescape do Jinja e tokens CSRF.
- Supply chain: dependencias fixadas + auditoria automatizavel.

## Auditoria de seguranca
```bash
pip install -r requirements-dev.txt
./scripts/security_audit.sh
```
No Windows:
```powershell
./scripts/security_audit.ps1
```

## Links de entrega 
- Repositorio: https://github.com/Lucasantunesribeiro/EmailTriageAI
- Video demonstrativo: https://www.youtube.com/watch?v=toFOr5ZTWUQ
- Deploy: http://100.48.50.86/

## Observacoes
- PDFs sao lidos com PyPDF2 e podem falhar em documentos com texto escaneado.
- O log nunca grava o conteudo completo do email.

## Estrutura
Veja a pasta `EmailTriageAI/` para detalhes de modulos, templates e scripts.
