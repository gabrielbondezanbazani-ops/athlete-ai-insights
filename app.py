import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import tempfile
import math
from fpdf import FPDF

# Inicializacao do MediaPipe Pose
import mediapipe.python.solutions.pose as mp_pose
import mediapipe.python.solutions.drawing_utils as mp_drawing

def calcular_angulo(a, b, c):
    """Calcula o angulo usando matemática escalar pura (evita erros de array)."""
    # a, b, c sao listas com duas coordenadas [x, y]
    ang = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
    ang = abs(ang)
    if ang > 180.0:
        ang = 360 - ang
    return float(ang)

def gerar_pdf(nome_atleta, modulo, insights, angulo_max, feedback_geral):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(30, 41, 59)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 12, "ATHLETE AI INSIGHTS REPORT", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 6, "Plataforma de Avaliacao Fisica e Biomecanica", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(18)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, f"Atleta Avaliado: {nome_atleta}", ln=True)
    pdf.cell(190, 8, f"Modulo Tecnologico: {modulo}", ln=True)
    pdf.cell(190, 8, f"Metrica Angular de Pico Obtida: {angulo_max:.1f} graus", ln=True)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(190, 10, "Diagnostico Computacional da IA:", ln=True)
    pdf.set_font("Arial", '', 11)
    for insight in insights:
        pdf.multi_cell(190, 7, f"- {insight}")
        pdf.ln(2)
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(190, 10, "Recomendacoes e Condutas Preventivas:", ln=True)
    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(190, 7, feedback_geral)
    pdf.set_y(-25)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(190, 10, "Este relatorio e gerado de forma automatizada e nao substitui laudo medico.", align='C')
    path_pdf = tempfile.mktemp(suffix=".pdf")
    pdf.output(path_pdf)
    return path_pdf

# Configuracao Base do Streamlit
st.set_page_config(page_title="Athlete AI Insights", page_icon="⚽", layout="wide")
st.title("📋 Athlete AI Insights REPORT")

st.sidebar.header("Parametros da Avaliacao")
nome_atleta = st.sidebar.text_input("Nome Completo do Atleta", "Jogador de Teste")
modulo = st.sidebar.selectbox("Módulo Biomecânico", ["Academia (Agachamento)", "Campo (Mecânica do Chute)"])
video_file = st.sidebar.file_uploader("Upload do Vídeo Executivo (.mp4, .mov)", type=["mp4", "mov"])

if video_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(video_file.read())
    cap = cv2.VideoCapture(tfile.name)
    stframe = st.empty()
    piores_metricas = []
    angulo_extremo = 180.0 if modulo == "Academia (Agachamento)" else 0.0
    valgo_detectado = False
    tronco_inclinado_detectado = False

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.resize(frame, (640, 480))
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                if modulo == "Academia (Agachamento)":
                    quadril = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    joelho = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    tornozelo = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                    
                    angulo = calcular_angulo(quadril, joelho, tornozelo)
                    if angulo < angulo_extremo: 
                        angulo_extremo = angulo
                    
                    if angulo > 90:
                        cv2.putText(image, "Aviso: Aumentar amplitude!", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    else:
                        cv2.putText(image, "Boa amplitude!", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        
                    # Valgo Dinâmico: Verifica se a posição X do joelho desvia horizontalmente do quadril
                    if abs(joelho[0] - quadril[0]) > 0.05:
                        valgo_detectado = True
                        cv2.putText(image, "ALERTA: Valgo Dinamico!", (40, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
                        
                elif modulo == "Campo (Mecânica do Chute)":
                    ombro = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    quadril = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    
                    # Cálculo escalar do tronco em relação à vertical
                    dx = ombro[0] - quadril[0]
                    dy = ombro[1] - quadril[1]
                    inclinacao = abs(math.degrees(math.atan2(dx, -dy)))
                    
                    if inclinacao > angulo_extremo: 
                        angulo_extremo = inclinacao
                    if inclinacao > 15:
                        tronco_inclinado_detectado = True
                        cv2.putText(image, "Tronco muito inclinado para tras!", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        cv2.putText(image, "Inclinacao correta do tronco", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            stframe.image(image, channels="BGR")
        cap.release()
        st.success("Processamento biomecanico finalizado!")
        
        if modulo == "Academia (Agachamento)":
            if angulo_extremo <= 90:
                piores_metricas.append("O atleta quebrou a paralela com sucesso.")
                feedback_geral = "Manter o volume de treino atual."
            else:
                piores_metricas.append("Foi observada amplitude insuficiente.")
                feedback_geral = "Inserir rotinas focadas em mobilidade de tornozelo."
            if valgo_detectado:
                piores_metricas.append("Risco de lesao ligamentar devido ao desvio de Valgo Dinamico.")
                feedback_geral += " Adicionar exercicios para fortalecimento."
        else:
            if tronco_inclinado_detectado:
                piores_metricas.append("Inclinacao excessiva do tronco para tras.")
                feedback_geral = "Realizar educativos de chute estacionario projetando o peito."
            else:
                piores_metricas.append("Mecanica postural correta.")
                feedback_geral = "Postura correta estabilizada."

        st.subheader("📊 Documentacao de Performance")
        pdf_path = gerar_pdf(nome_atleta, modulo, piores_metricas, angulo_extremo, feedback_geral)
        with open(pdf_path, "rb") as f:
            st.download_button(label="Download Relatorio PDF", data=f, file_name="Relatorio.pdf", mime="application/pdf")
