import subprocess

def run_libcamera_hello():
    try:
        print("🎥 패스파인더 카메라 테스트 시작!")
        print("📷 libcamera-hello를 실행합니다...")
        print("💡 Ctrl+C로 종료하세요")
        print("-" * 40)
        process = subprocess.Popen(
            ['libcamera-hello'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # 실시간 출력
        for line in process.stdout:
            print(line, end='')

        process.wait()

        if process.returncode != 0:
            print(f"\n[오류] libcamera-hello 종료 코드: {process.returncode}")

    except FileNotFoundError:
        print("▶ libcamera-hello 명령어를 찾을 수 없습니다.")

if __name__ == "__main__":
    run_libcamera_hello()
