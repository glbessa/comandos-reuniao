import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyvirtualcam
import math
import os
import sys
import numpy as np


def get_resource_path(relative_path):
    """
    Retorna o caminho absoluto do recurso, funcionando tanto em desenvolvimento
    quanto dentro do executável gerado pelo PyInstaller (_MEIPASS).
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


FACE_MODEL_PATH = get_resource_path("face_landmarker.task")
HAND_MODEL_PATH = get_resource_path("hand_landmarker.task")
IMAGE_PATH = get_resource_path("imagem_padrao.jpg")


def setup_detectors():
    base_options_face = python.BaseOptions(model_asset_path=FACE_MODEL_PATH)
    options_face = vision.FaceLandmarkerOptions(
        base_options=base_options_face,
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1
    )
    face_detector = vision.FaceLandmarker.create_from_options(options_face)

    base_options_hand = python.BaseOptions(model_asset_path=HAND_MODEL_PATH)
    options_hand = vision.HandLandmarkerOptions(
        base_options=base_options_hand,
        running_mode=vision.RunningMode.IMAGE,
        num_hands=1
    )
    hand_detector = vision.HandLandmarker.create_from_options(options_hand)

    return face_detector, hand_detector


def is_shh_gesture(hand_landmarks, face_landmarks, frame_w, frame_h):
    """
    Verifica se:
    1. Apenas o indicador está estendido (médio, anelar e mínimo fechados)
    2. A ponta do indicador (landmark 8) está na proximidade dos lábios (landmark 13)
    """
    # Ponta do indicador (8)
    tip_x = int(hand_landmarks[8].x * frame_w)
    tip_y = int(hand_landmarks[8].y * frame_h)

    # Centro dos lábios (13)
    lip_x = int(face_landmarks[13].x * frame_w)
    lip_y = int(face_landmarks[13].y * frame_h)

    dist_to_mouth = math.hypot(tip_x - lip_x, tip_y - lip_y)

    # Dedos dobrados: ponta abaixo da articulação (em pixels, Y cresce para baixo)
    medio_dobrado = hand_landmarks[12].y > hand_landmarks[10].y
    anelar_dobrado = hand_landmarks[16].y > hand_landmarks[14].y
    minimo_dobrado = hand_landmarks[20].y > hand_landmarks[18].y

    # Indicador estendido: ponta acima da articulação
    indicador_em_pe = hand_landmarks[8].y < hand_landmarks[6].y

    # Raio de proximidade da boca proporcional ao frame (10% da largura)
    raio_boca = frame_w * 0.10

    dedos_corretos = indicador_em_pe and medio_dobrado and anelar_dobrado and minimo_dobrado
    dedo_na_boca = dist_to_mouth < raio_boca

    return dedos_corretos and dedo_na_boca


def is_open_palm_gesture(hand_landmarks):
    """
    Verifica se os 5 dedos estão abertos/estendidos (palma aberta/sinal de pare).
    """
    # Pontas e articulações intermediárias (MCP ou PIP)
    # Polegar: distância da ponta (4) em relação ao pulso (0) vs articulação (2) em relação ao pulso
    pulso = hand_landmarks[0]
    polegar_tip = hand_landmarks[4]
    polegar_mcp = hand_landmarks[2]

    dist_polegar_tip = math.hypot(polegar_tip.x - pulso.x, polegar_tip.y - pulso.y)
    dist_polegar_mcp = math.hypot(polegar_mcp.x - pulso.x, polegar_mcp.y - pulso.y)
    polegar_aberto = dist_polegar_tip > dist_polegar_mcp * 1.2

    # Demais 4 dedos: ponta acima da articulação (y menor que articulação)
    indicador_aberto = hand_landmarks[8].y < hand_landmarks[6].y
    medio_aberto = hand_landmarks[12].y < hand_landmarks[10].y
    anelar_aberto = hand_landmarks[16].y < hand_landmarks[14].y
    minimo_aberto = hand_landmarks[20].y < hand_landmarks[18].y

    return polegar_aberto and indicador_aberto and medio_aberto and anelar_aberto and minimo_aberto


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro: Não foi possível abrir a webcam real.")
        return

    face_detector, hand_detector = setup_detectors()

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 0 or fps > 60:
        fps = 30

    caminho_imagem = "imagem_padrao.jpg" if os.path.exists("imagem_padrao.jpg") else IMAGE_PATH
    if os.path.exists(caminho_imagem):
        padrao = cv2.imread(caminho_imagem)
        padrao_resized = cv2.resize(padrao, (width, height))
    else:
        print("Aviso: 'imagem_padrao.jpg' não encontrada. Usando tela preta como padrão.")
        padrao_resized = np.zeros((height, width, 3), dtype=np.uint8)

    alpha = 0.0
    desaparecendo = False
    velocidade_fade = 0.04
    frames_shh = 0
    frames_palma = 0
    FRAMES_NECESSARIOS = 4

    print(f"Iniciando Câmera Virtual: {width}x{height} @ {fps}fps")

    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=fps, fmt=pyvirtualcam.PixelFormat.RGB) as vcam:
            print(f"Câmera virtual ativa em: {vcam.device}")
            print("Gesto 'Shh': desaparece | Gesto 'Palma aberta': reaparece | 'Q': sair")

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                face_result = face_detector.detect(mp_image)
                hand_result = hand_detector.detect(mp_image)

                gesto_shh = False
                gesto_palma = False

                if hand_result.hand_landmarks:
                    hand_lms = hand_result.hand_landmarks[0]

                    # 1. Verifica palma aberta (reaparecer)
                    if is_open_palm_gesture(hand_lms):
                        gesto_palma = True

                    # 2. Verifica shh (desaparecer) se o rosto estiver detectado
                    if face_result.face_landmarks and not gesto_palma:
                        face_lms = face_result.face_landmarks[0]
                        if is_shh_gesture(hand_lms, face_lms, width, height):
                            gesto_shh = True

                # Atualiza contadores de persistência de gesto
                if gesto_shh:
                    frames_shh += 1
                    if frames_shh >= FRAMES_NECESSARIOS:
                        desaparecendo = True
                else:
                    frames_shh = 0

                if gesto_palma:
                    frames_palma += 1
                    if frames_palma >= FRAMES_NECESSARIOS:
                        desaparecendo = False
                else:
                    frames_palma = 0

                if desaparecendo:
                    alpha = min(1.0, alpha + velocidade_fade)
                else:
                    alpha = max(0.0, alpha - velocidade_fade)

                frame_final = cv2.addWeighted(frame, 1.0 - alpha, padrao_resized, alpha, 0)
                frame_final_rgb = cv2.cvtColor(frame_final, cv2.COLOR_BGR2RGB)

                vcam.send(frame_final_rgb)
                vcam.sleep_until_next_frame()

                status_txt = f"{'DESAPARECENDO (SHH!)' if desaparecendo else 'NORMAL'} ({int(alpha * 100)}%)"
                cor_status = (0, 0, 255) if desaparecendo else (0, 255, 0)
                cv2.putText(frame_final, status_txt, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor_status, 2)
                cv2.putText(frame_final, "[R] Reaparecer | [Q] Sair", (20, height - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

                cv2.imshow("Controle - Comandos Reuniao", frame_final)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    desaparecendo = False

    except Exception as e:
        print(f"Erro ao inicializar câmera virtual: {e}")
        print("Certifique-se de que o v4l2loopback está carregado no sistema.")

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
