import streamlit as st
import os
import tempfile
import zipfile
import io
from pydub import AudioSegment

def calculate_split_points(file_path, target_size):
    # 오디오 파일에서 비트레이트(kbps) 추출
    audio = AudioSegment.from_file(file_path)
    bitrate = audio.frame_rate * audio.channels * audio.sample_width * 8 / 1000  # kbps
    
    # 각 분할에 대한 최대 지속 시간 계산
    max_duration = (target_size * 1024 * 1024 * 8) / (bitrate * 1000)  # 초 단위
    return max_duration

def split_audio(file_path, target_size, output_dir, original_filename):
    # 오디오 파일 로드
    audio = AudioSegment.from_file(file_path)
    max_duration = calculate_split_points(file_path, target_size) * 1000  # 밀리초로 변환
    
    # 오디오를 청크로 분할
    chunks = [audio[i:i + int(max_duration)] for i in range(0, len(audio), int(max_duration))]
    
    # 새 파일명으로 청크 저장
    base_name, ext = os.path.splitext(original_filename)
    output_files = []
    
    for idx, chunk in enumerate(chunks):
        output_file = os.path.join(output_dir, f"{base_name}_size_adjusted_part{idx+1}{ext}")
        chunk.export(output_file, format=ext[1:])
        output_files.append(output_file)
    
    return output_files

def main():
    st.title("오디오 파일 용량 조정 도구")
    st.write("오디오 파일을 지정된 크기로 분할하는 애플리케이션입니다.")
    
    # 목표 파일 크기 설정 (MB 단위)
    target_size = st.number_input("목표 파일 크기 (MB)", min_value=1, value=29, step=1)
    
    # 파일 업로더
    uploaded_files = st.file_uploader("오디오 파일 업로드 (여러 파일 선택 가능)", 
                                     type=["mp3", "wav", "ogg", "flac"], 
                                     accept_multiple_files=True)
    
    if uploaded_files and st.button("파일 처리 시작"):
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 처리 과정 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            processed_files = []
            
            # 각 파일 처리
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"처리 중: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
                
                # 임시 파일에 업로드된 파일 저장
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 오디오 파일 분할
                output_files = split_audio(temp_path, target_size, temp_dir, uploaded_file.name)
                processed_files.extend(output_files)
                
                # 진행률 업데이트
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_text.text("모든 파일 처리 완료! 다운로드 준비 중...")
            
            # 결과 파일들을 ZIP으로 압축
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for file_path in processed_files:
                    file_name = os.path.basename(file_path)
                    zip_file.write(file_path, file_name)
            
            # 다운로드 버튼 생성
            zip_buffer.seek(0)
            st.download_button(
                label="처리된 파일 다운로드 (ZIP)",
                data=zip_buffer,
                file_name="processed_audio_files.zip",
                mime="application/zip"
            )
            
            status_text.text("완료! ZIP 파일을 다운로드하세요.")

if __name__ == "__main__":
    main()
