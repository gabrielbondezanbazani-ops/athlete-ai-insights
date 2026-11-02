import streamlit as st
import cv2
from cvzone.PoseModule import PoseDetector
import numpy as np
import tempfile
import math
from fpdf import FPDF

def calcular_angulo(a, b, c):
    """Calcula o angulo usando pontos escalares simples."""
    ang = math.degrees(math.atan2(c[1] - b[1], c[1] - b[0]) - math.atan2(a[1] - b[1], a[1] - b[0]))
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

    # Inicializa o detector ultra-estavel do cvzone
    detector = PoseDetector()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.resize(frame, (640, 480))
        
        # Encontra o corpo e desenha o esqueleto anatômico
        frame = detector.findPose(frame)
        lmList, bboxInfo = detector.findPosition(frame, bboxWithHands=False)
        
        if lmList:
            if modulo == "Academia (Agachamento)":
                # Pontos esquerdo: Quadril (24), Joelho (26), Tornozelo (28)
                quadril = lmList[24][1:3]
                joelho = lmList[26][1:3]
                tornozelo = lmList[28][1:3]
                
                angulo = calcular_angulo(quadril, joelho, tornozelo)
                if angulo < angulo_extremo: 
                    angulo_extremo = angulo
                
                if angulo > 90:
                    cv2.putText(frame, "Aviso: Aumentar amplitude!", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, "Boa amplitude!", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                if abs(joelho[0] - quadril[0]) > 25:
                    valgo_detectado = True
                    cv2.putText(frame, "ALERTA: Valgo Dinamico!", (40, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
                    
            elif modulo == "Campo (Mecânica do Chute)":
                # Pontos esquerdo: Ombro (12), Quadril (24)
                ombro = lmList[12][1:3]
                quadril = lmList[24][1:3]
                
                inclinacao = abs(math.degrees(math.atan2(ombro[0] - quadril[0], quadril[1] - ombro[1])))
                if inclinacao > angulo_extremo: 
                    angulo_extremo = inclinacao
                if inclinacao > 15:
                    tronco_inclinado_detectado = True
                    cv2.putText(frame, "Tronco muito inclinado para tras!", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, "Inclinacao correta do tronco", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        stframe.image(frame, channels="BGR")
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
