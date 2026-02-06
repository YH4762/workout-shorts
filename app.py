import streamlit as st
import google.generativeai as genai
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image
import tempfile
import os
import random

# 1. 페이지 설정
st.set_page_config(page_title="영환님의 AI 와드 쇼츠 제작기", layout="wide")

# --- API 키 설정 ---
# Streamlit Secrets에 api_key를 등록했다면 그것을 사용하고, 없으면 직접 입력한 값을 사용합니다.
if "api_key" in st.secrets:
    GEMINI_API_KEY = st.secrets["api_key"]
else:
    # 직접 입력 시 여기에 영환님의 API 키를 넣으세요
    GEMINI_API_KEY = "AIzaSy..." 

genai.configure(api_key=GEMINI_API_KEY)

st.title("🏋️ 영환님의 AI 와드 쇼츠 제작기 (Star Wars Edition)")
st.info("안정적인 분석을 위해 Gemini 1.5 Flash 모델을 사용합니다.")

# 2. 파일 업로드 섹션
st.subheader("1. 소스 파일 업로드")
col1, col2 = st.columns(2)

with col1:
    wod_photo = st.file_uploader("📸 와드 사진 (JPG/PNG)", type=['jpg', 'png', 'jpeg'])
with col2:
    workout_videos = st.file_uploader("🎥 운동 영상들 (MP4) - 여러 개 선택 가능", type=['mp4', 'mov'], accept_multiple_files=True)

# 3. AI 와드 분석 로직 (404 에러 방지 포함)
if wod_photo:
    img = Image.open(wod_photo)
    st.image(img, caption="업로드된 와드 사진", width=300)
    
    if st.button("🔍 AI 와드 분석 시작"):
        with st.spinner("AI가 사진을 분석 중입니다..."):
            # 가장 호환성이 높은 모델 명칭 시도
            model_names = ["gemini-1.5-flash", "models/gemini-1.5-flash"]
            success = False
            
            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name=m_name)
                    prompt = """이 사진 속의 크로스핏 와드 내용을 추출해줘. 
                    스타워즈 오프닝 크롤처럼 [EPISODE: 오늘날짜] 형태의 제목과 
                    운동 목록을 아주 간결하고 멋지게 리스트로 작성해줘."""
                    
                    response = model.generate_content([prompt, img])
                    st.session_state['extracted_wod'] = response.text
                    success = True
                    break
                except Exception:
                    continue
            
            if success:
                st.success("분석 완료!")
            else:
                st.error("모델을 찾을 수 없거나 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요.")

# 4. 분석 결과 수정 및 스타워즈 영상 제작
if 'extracted_wod' in st.session_state:
    st.subheader("2. 자막 확인 및 쇼츠 제작")
    final_text = st.text_area("스타워즈 자막 내용 (수정 가능)", value=st.session_state['extracted_wod'], height=200)
    
    if st.button("🚀 스타워즈 쇼츠 제작 시작"):
        if workout_videos:
            with st.spinner("영상을 편집하고 자막을 합성 중입니다..."):
                final_clips = []
                
                for uploaded_file in workout_videos:
                    try:
                        # 임시 파일 저장
                        t_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                        t_input.write(uploaded_file.read())
                        t_input_path = t_input.name
                        t_input.close()
                        
                        clip = VideoFileClip(t_input_path)
                        
                        # 3초 하이라이트 랜덤 추출
                        if clip.duration > 3:
                            start_time = random.uniform(0, clip.duration - 3)
                            highlight = clip.subclip(start_time, start_time + 3)
                            final_clips.append(highlight)
                        else:
                            final_clips.append(clip)
                            
                    except Exception as e:
                        st.warning(f"영상 처리 중 오류: {uploaded_file.name}")
                
                if final_clips:
                    # 모든 하이라이트 합치기
                    combined_video = concatenate_videoclips(final_clips)
                    W, H = combined_video.w, combined_video.h
                    
                    # 스타워즈 스타일 흐르는 자막 생성
                    txt_clip = TextClip(
                        text=final_text,
                        font="Arial", # 서버 환경에 따라 기본 폰트 사용
                        color='yellow',
                        method='caption',
                        size=(int(W * 0.8), None)
                    ).with_duration(combined_video.duration)

                    # 아래에서 위로 흐르는 애니메이션 함수
                    def star_wars_scroll(t):
                        # 시작 위치: 화면 아래 끝, 끝 위치: 화면 위 끝너머
                        y_pos = int(H - (H + txt_clip.h + 100) * (t / combined_video.duration))
                        return ('center', y_pos)

                    final_video = CompositeVideoClip([
                        combined_video, 
                        txt_clip.with_position(star_wars_scroll)
                    ])
                    
                    output_path = "starwars_wod_final.mp4"
                    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
                    
                    with open(output_path, "rb") as f:
                        st.download_button("✅ 쇼츠 다운로드 하기", f, file_name="My_WOD_StarWars.mp4")
                    
                    # 클립 닫기
                    combined_video.close()
                else:
                    st.error("처리된 영상이 없습니다.")
        else:
            st.warning("🎥 운동 영상을 업로드해 주세요!")
