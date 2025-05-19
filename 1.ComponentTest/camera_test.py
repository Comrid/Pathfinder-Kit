import subprocess

def run_libcamera_hello():
    try:
        result = subprocess.run(
            ['libcamera-hello'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # str로 출력되게 함 (Python 3.7 이상)
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("▶ libcamera-hello 실행 중 오류 발생:")
        print(e.stderr)  # stderr 그대로 출력
    except FileNotFoundError:
        print("▶ libcamera-hello 명령어를 찾을 수 없습니다.")

if __name__ == "__main__":
    run_libcamera_hello()
