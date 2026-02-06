import streamlit as st
import google.generativeai as genai
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from PIL import Image
import tempfile
import os

# 1. 페이지 설정
st.set_page_config(page_title="영환님의 AI 와드 쇼츠 제작기", layout="centered")

# --- 설정 섹션 (영환님의 API 키를 여기에 입력하세요) ---
GEMINI_API_KEY = "AIzaSyCglhN8CBvm2O2ClKuJjMce2H0uNGhVda0" 
genai.configure(api_key=GEMINI_API_KEY)
# --------------------------------------------------

st.title("🏋️ 영환님의 AI 와드 쇼츠 제작기")
st.write("사진을 올리면 Gemini 2.0이 와드를 읽고 영상에 자막을 입혀줍니다.")

# 2. 파일 업로드 섹션
st.subheader("1. 소스 파일 업로드")
col1, col2 = st.columns(2)

with col1:
    wod_photo = st.file_uploader("📸 와드 사진 (JPG/PNG)", type=['jpg', 'png', 'jpeg'])
with col2:
    workout_video = st.file_uploader("🎥 운동 영상 (MP4)", type=['mp4', 'mov'])

# 3. AI 와드 분석 로직
if wod_photo:
    img = Image.open(wod_photo)
    st.image(img, caption="업로드된 와드 사진", width=300)
    
    if st.button("🔍 AI 와드 분석 시작"):
        with st.spinner("Gemini 2.0 Flash가 사진을 분석 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                prompt = "이 사진에서 크로스핏 와드 내용을 추출해줘. 운동 명칭과 횟수만 불필요한 말 없이 깔끔한 리스트 형식으로 써줘."
                response = model.generate_content([prompt, img])
                st.session_state['extracted_wod'] = response.text
                st.success("분석 완료!")
            except Exception as e:
                st.error(f"AI 분석 중 오류 발생: {e}")

# 4. 분석 결과 수정 및 영상 제작
if 'extracted_wod' in st.session_state:
    st.subheader("2. 와드 내용 확인 및 제작")
    # AI가 분석한 내용을 영환님이 최종 수정할 수 있는 창
    final_text = st.text_area("자막으로 들어갈 내용입니다 (수정 가능)", 
                             value=st.session_state['extracted_wod'], height=200)
    
    speed_factor = st.slider("자막 스크롤 속도", 0.5, 3.0, 1.3)

    if st.button("🚀 최종 쇼츠 제작 시작"):
        if workout_video:
            with st.spinner("영상을 렌더링 중입니다. 약 1~2분 정도 소요됩니다..."):
                # 임시 파일 저장
                t_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                t_input.write(workout_video.read())
                
                # MoviePy 편집 시작
                clip = VideoFileClip(t_input.name)
                # 숏폼을 위해 앞부분 15초만 자르거나 전체 사용 (여기선 15초 예시)
                clip = clip.subclipped(0, min(15, clip.duration))
                
                W, H = clip.w, clip.h
                
                # 자막 클립 생성
                txt_clip = TextClip(
                    text=final_text,
                    font_size=int(H * 0.04),
                    color='yellow',
                    method='caption',
                    size=(int(W * 0.8), None)
                ).with_duration(clip.duration)

                # 스크롤 효과 함수
                def scroll_effect(t):
                    total_distance = H + txt_clip.h
                    y_pos = int(H - total_distance * (t / (clip.duration / speed_factor)))
                    return ('center', y_pos)

                moving_txt = txt_clip.with_position(scroll_effect)
                
                # 합성 및 출력
                final_video = CompositeVideoClip([clip, moving_txt])
                output_path = "yh_result.mp4"
                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
                
                # 결과 다운로드 버튼
                with open(output_path, "rb") as f:
                    st.download_button("✅ 완성! 영상 저장하기", f, file_name="WOD_Shorts.mp4")
                
                # 임시 파일 삭제
                os.unlink(t_input.name)
        else:
            st.warning("운동 영상 파일을 먼저 업로드해주세요!")