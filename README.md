# Gerador de vídeos curtos

Aplicativo Streamlit para criar vários vídeos verticais (9:16) com:
- fundo enviado pelo usuário (imagem);
- texto/roteiro na tela;
- narração automática em português, inglês ou espanhol;
- quatro estilos visuais;
- exportação dos vídeos em MP4 e pacote ZIP.

## Como executar em um computador ou ambiente Linux na nuvem

```bash
pip install -r requirements.txt
streamlit run webui/Main.py --server.address 0.0.0.0
```

## Publicar para acessar pelo iPhone

1. Crie uma conta no GitHub e um repositório novo.
2. Envie todos os arquivos desta pasta para o repositório, mantendo `webui/Main.py` e `requirements.txt`.
3. Entre em https://share.streamlit.io/ e conecte o GitHub.
4. Escolha o repositório, selecione `webui/Main.py` como arquivo principal e publique.
5. Abra o endereço público gerado pelo Streamlit no Safari do iPhone.

Não use `http://localhost:8501` no Safari do iPhone para acessar um servidor que está em outro dispositivo. `localhost` sempre aponta para o próprio aparelho.

## Como usar

1. Escreva um roteiro por vídeo.
2. Separe os roteiros com uma linha contendo apenas `---`.
3. A primeira linha de cada roteiro é o título; as linhas seguintes são a narração.
4. Envie uma ou mais imagens de fundo. O aplicativo alterna os fundos.
5. Escolha o modelo e o idioma e toque em **Gerar vídeos**.
6. Baixe o ZIP com os MP4.

## Observações importantes

- A narração automática requer internet.
- Se enviar um áudio próprio, ele será usado em todos os vídeos da geração.
- O texto aparece como cartão de texto durante o vídeo; esta versão não faz transcrição palavra por palavra sincronizada.
- O processamento de vídeo pode consumir bastante memória e tempo. Em hospedagens gratuitas, comece com um ou dois vídeos curtos.
- Use apenas imagens, vídeos, músicas e áudios que você tenha autorização para utilizar.
