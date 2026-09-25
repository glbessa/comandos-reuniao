# Comandos Reunião (Câmera com Fade por Gestos)

Sistema de câmera virtual inteligente para reuniões online (Google Meet, Zoom, Microsoft Teams, Discord). Permite desaparecer suavemente (efeito fade/crossfade) ao fazer um gesto de **"shh"** e reaparecer ao mostrar a **palma da mão aberta**.

---

## 🖐️ Gestos Reconhecidos

| Gesto | Ação | Descrição |
|---|---|---|
| 🤫 **"Shh"** | **Desaparecer** (Fade Out) | Dedo indicador na frente dos lábios (com os demais dedos fechados). Transiciona para a imagem padrão ou tela preta. |
| ✋ **Palma Aberta** | **Reaparecer** (Fade In) | Mão inteira aberta (5 dedos estendidos). Retorna suavemente para a câmera em tempo real. |

### Atalhos no Teclado (Janela de Preview)
- `R`: Forçar reaparecer.
- `Q`: Encerrar o programa.

---

## 🖼️ Imagem Padrão Customizada (Opcional)

Se desejar transicionar para uma foto sua parada (ou qualquer outra imagem), basta colocar um arquivo chamado **`imagem_padrao.jpg`** na raiz do projeto. Caso esse arquivo não exista, o sistema fará a transição para uma **tela preta limpa**.

---

## 🐧 Setup no Linux (Ubuntu / Pop!_OS / Debian)

### 1. Pré-requisitos do Sistema (Módulo de Câmera Virtual)
Instale o módulo de kernel `v4l2loopback` e ferramentas de vídeo:

```bash
sudo apt update
sudo apt install -y v4l2loopback-dkms v4l-utils
```

Carregue o módulo criando o dispositivo virtual `/dev/video20`:
```bash
sudo modprobe v4l2loopback devices=1 video_nr=20 card_label="Camera Virtual" exclusive_caps=1
```

> **Dica (Persistir após reiniciar o PC):**
> Crie o arquivo `/etc/modprobe.d/v4l2loopback.conf` com o conteúdo:
> ```ini
> options v4l2loopback devices=1 video_nr=20 card_label="Camera Virtual" exclusive_caps=1
> ```
> E adicione `v4l2loopback` ao final de `/etc/modules`.

### 2. Configurar o Ambiente Python

```bash
# Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Modelos do MediaPipe
Os modelos `.task` já devem estar na pasta do projeto. Se precisar baixá-los manualmente:
```bash
curl -s -L -o face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
curl -s -L -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

### 4. Executar
```bash
python main.py
```
Nas configurações de vídeo do Google Meet, Zoom ou Teams, selecione **"Camera Virtual"**.

---

## 🪟 Setup no Windows

### 1. Pré-requisitos do Sistema (Driver de Câmera Virtual)
No Windows, o `pyvirtualcam` utiliza o driver de câmera virtual do OBS Studio:

1. Baixe e instale o [OBS Studio](https://obsproject.com/).
2. Abra o OBS Studio uma vez para que o Windows registre a `OBS Virtual Camera` no sistema (não é necessário deixar o OBS aberto durante o uso).
   - *Alternativa sem instalar o OBS completo:* Instale apenas o driver standalone via [obs-virtual-cam releases](https://github.com/Fenrirthviti/obs-virtual-cam/releases).

### 2. Configurar o Ambiente Python (PowerShell)

```powershell
# Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instale as dependências
pip install -r requirements.txt
```

### 3. Modelos do MediaPipe (PowerShell)
Baixe os modelos para a pasta do projeto:
```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task" -OutFile "face_landmarker.task"
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task" -OutFile "hand_landmarker.task"
```

### 4. Executar
```powershell
python main.py
```
Nas configurações de vídeo do Google Meet, Zoom ou Teams, selecione **"OBS Virtual Camera"**.

---

## 📦 Gerando o Executável (.exe) para Windows

Se desejar gerar o arquivo executável para distribuir sem precisar de Python instalado:

```powershell
pip install pyinstaller

pyinstaller --noconfirm --onedir --windowed `
  --name "ComandosReuniao" `
  --add-data "face_landmarker.task;." `
  --add-data "hand_landmarker.task;." `
  --collect-all mediapipe `
  --collect-all pyvirtualcam `
  main.py
```

O executável pronto ficará em `dist/ComandosReuniao/ComandosReuniao.exe`.

---

## 🚀 Releases Automáticas (GitHub Actions)

O repositório já conta com o workflow em `.github/workflows/release.yml`. Para gerar automaticamente uma Release com o `.zip` do executável Windows:

1. Faça commit e push das alterações:
   ```bash
   git add .
   git commit -m "Nova versão"
   git push origin main
   ```
2. Crie e envie uma tag de versão (ex: `v1.0.0`):
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. O GitHub Actions iniciará uma máquina Windows, instalará as dependências, compilará o `.exe`, compactará em `ComandosReuniao-Windows-x64.zip` e criará a **Release** automaticamente na aba **Releases** do GitHub!

---

## ⚙️ Ajustes e Parâmetros (`main.py`)

No arquivo `main.py`, você pode ajustar parâmetros como:
- `velocidade_fade = 0.04`: Aumente para desaparecer mais rápido, ou diminua para uma transição mais lenta.
- `FRAMES_NECESSARIOS = 4`: Quantidade de frames consecutivos em que o gesto deve ser detectado para evitar acionamentos acidentais.
- `IMAGE_PATH`: Nome do arquivo da imagem para a qual transicionar.
