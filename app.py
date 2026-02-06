import streamlit as st
import google.generativeai as genai
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image
import tempfile
import os
import random # 하이라이트 랜덤 추출용

# 1. 페이지 설정
st.set_page_config(page_title="영환님의 AI 와드 쇼츠 제작기 (스타워즈 에디션)", layout="wide")

# --- 설정 섹션 (영환님의 API 키를 여기에 입력하세요) ---
GEMINI_API_KEY = "YOUR_GOOGLE_API_KEY" # 영환님의 실제 키로 변경하세요!
genai.configure(api_key=GEMINI_API_KEY)
# --------------------------------------------------

st.title("🏋️ 영환님의 AI 와드 쇼츠 제작기")
st.subheader("🌠 스타워즈 스타일 와드 쇼츠를 만들 시간!")
st.write("와드 사진을 올리면 Gemini 2.0 Flash가 와드를 읽고, 여러 운동 영상에서 하이라이트를 뽑아 스타워즈 자막으로 쇼츠를 만들어줍니다.")

# 2. 소스 파일 업로드 섹션
st.subheader("1. 소스 파일 업로드")
col1, col2 = st.columns(2)

with col1:
    wod_photo = st.file_uploader("📸 와드 사진 (JPG/PNG)", type=['jpg', 'png', 'jpeg'])
with col2:
    # 여러 영상 파일 업로드 가능
    workout_videos = st.file_uploader("🎥 운동 영상들 (MP4) - 여러 개 선택 가능", type=['mp4', 'mov'], accept_multiple_files=True)

# 3. AI 와드 분석 로직
if wod_photo:
    img = Image.open(wod_photo)
    st.image(img, caption="업로드된 와드 사진", width=300)
    
    if st.button("🔍 AI 와드 분석 시작"):
        with st.spinner("Gemini 2.0 Flash가 사진을 분석 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                prompt = """
                이 사진에서 크로스핏 와드 내용을 추출해줘. 
                운동 명칭과 횟수 또는 특이사항을 불필요한 말 없이 깔끔한 리스트 또는 표 형식으로 요약해줘. 
                스타워즈 오프닝 크롤에 들어갈 것처럼 제목과 내용을 구분해서 간결하게 작성해줘.
                예시:
                [EPISODE 1: 새로운 희망]
                오늘은 힘든 와드가 기다리고 있다.
                - 스쿼트: 10회
                - 풀업: 5회
                """
                response = model.generate_content([prompt, img])
                st.session_state['extracted_wod'] = response.text
                st.success("분석 완료!")
            except Exception as e:
                st.error(f"AI 분석 중 오류 발생: {e}")

# 4. 분석 결과 수정 및 영상 제작
if 'extracted_wod' in st.session_state:
    st.subheader("2. 와드 내용 확인 및 쇼츠 제작")
    
    final_text = st.text_area("스타워즈 스타일 자막으로 들어갈 내용입니다 (수정 가능)", 
                             value=st.session_state['extracted_wod'], height=300)
    
    # 스타워즈 자막용 폰트 사이즈 및 시작 위치 조절
    font_size_start = st.slider("자막 시작 글자 크기 (원근감)", 30, 80, 50)
    scroll_speed = st.slider("자막 스크롤 속도", 0.5, 2.0, 1.0) # 기본 1.0
    
    if st.button("🚀 스타워즈 쇼츠 제작 시작"):
        if workout_videos:
            with st.spinner("영상을 렌더링 중입니다. 운동량에 따라 수 분 소요될 수 있습니다..."):
                final_clips = []
                total_duration = 0 # 전체 영상 길이 계산
                
                # 각 영상에서 3초 하이라이트 추출
                for uploaded_file in workout_videos:
                    try:
                        t_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                        t_input.write(uploaded_file.read())
                        t_input_path = t_input.name
                        t_input.close() # 파일 핸들 닫기
                        
                        clip = VideoFileClip(t_input_path)
                        
                        # 영상 길이가 3초 이상일 때만 하이라이트 추출
                        if clip.duration > 3:
                            start_time = random.uniform(0, clip.duration - 3) # 랜덤 시작점
                            highlight_clip = clip.subclip(start_time, start_time + 3)
                            final_clips.append(highlight_clip)
                            total_duration += 3
                        else:
                            # 3초 미만이면 전체 클립 사용
                            final_clips.append(clip)
                            total_duration += clip.duration
                        
                        clip.close() # 사용 후 클립 닫기
                        os.unlink(t_input_path) # 임시 파일 삭제
                    except Exception as e:
                        st.warning(f"영상 파일 처리 중 오류 발생: {uploaded_file.name} - {e}")
                        
                if not final_clips:
                    st.error("처리할 수 있는 영상 파일이 없습니다. 다시 확인해주세요.")
                    st.stop()
                
                # 모든 하이라이트 클립 합치기
                if len(final_clips) > 1:
                    combined_video = concatenate_videoclips(final_clips)
                else:
                    combined_video = final_clips[0]

                W, H = combined_video.w, combined_video.h
                
                # 스타워즈 스타일 자막 (원근감 및 스크롤)
                def star_wars_scroll(t):
                    # 시작점은 화면 아래쪽 + 글자 길이만큼
                    start_y = H * 1.5 
                    end_y = -txt_clip.h * 0.5 # 화면 위로 사라지도록
                    
                    # 스크롤 비율 (t는 0부터 duration까지)
                    scroll_progress = (t * scroll_speed) / combined_video.duration
                    
                    # 선형 보간으로 y 위치 계산
                    y_pos = int(start_y - (start_y - end_y) * scroll_progress)
                    
                    # 글자 크기 변화 (원근감)
                    # 스크롤되는 동안 글자 크기가 작아지게
                    font_size_current = max(int(font_size_start * (1 - scroll_progress * 0.5)), 15) # 최소 15
                    
                    return txt_clip.set_position(('center', y_pos)).set_fontsize(font_size_current)

                # 텍스트 클립 생성 (기본 폰트, 나중에 폰트 추가 가능)
                txt_clip = TextClip(
                    text=final_text,
                    font="Arial", # 스타워즈 분위기 낼 폰트 (예: 'Star Jedi', 설치 필요)
                    color='yellow',
                    method='caption',
                    size=(int(W * 0.7), None) # 화면 폭의 70% 사용
                ).with_duration(combined_video.duration)

                # 폰트 색상을 스타워즈에 맞게 황금색으로 조정
                # txt_clip = txt_clip.set_stroke(color='gold', width=0.5)

                final_video = CompositeVideoClip([combined_video, txt_clip.fx(star_wars_scroll)])
                
                output_path = "yh_starwars_wod.mp4"
                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
                
                with open(output_path, "rb") as f:
                    st.download_button("✅ 완성! 스타워즈 쇼츠 저장하기", f, file_name="WOD_StarWars_Shorts.mp4")
                
                # 임시 파일 삭제
                # os.unlink(t_input.name) # 각 클립 처리 시 삭제 완료
        else:
            st.warning("운동 영상 파일을 하나 이상 업로드해주세요!")
