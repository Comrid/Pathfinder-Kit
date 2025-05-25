# 패스파인더 키트 OS 설치 및 SSH 설정 가이드

## 🎯 개요
이 가이드는 Raspberry Pi Zero 2 W에 운영체제를 설치하고 원격 접속을 설정하는 과정을 안내합니다.

## 📋 준비물
- [ ] **microSD 카드** (Class 10, 16GB 이상 권장)
- [ ] **SD 카드 리더기** (컴퓨터 연결용)
- [ ] **컴퓨터** (Windows, macOS, Linux)
- [ ] **Wi-Fi 네트워크 정보** (SSID, 비밀번호)

## 💾 1단계: Raspberry Pi OS 다운로드 및 설치

### Raspberry Pi Imager 설치
1. [공식 사이트](https://www.raspberrypi.com/software/)에서 Raspberry Pi Imager 다운로드
2. 운영체제에 맞는 버전 설치 (Windows/macOS/Linux)

### OS 이미지 작성
1. **SD 카드를 컴퓨터에 삽입** (최소 16GB 권장)
2. **Raspberry Pi Imager 실행**
3. **OS 선택**:
   ```
   Raspberry Pi OS (other) → Raspberry Pi OS Lite (32-bit)
   ```
   > 💡 **Lite 버전 권장 이유**: Pi Zero 2 W의 제한된 메모리(512MB)에 최적화

4. **저장소 선택**: microSD 카드 선택
5. **고급 설정** (⚙️ 아이콘 클릭):

### 🔧 고급 설정 구성
```
✅ SSH 활성화
   - 비밀번호 인증 사용
   - 사용자명: pi
   - 비밀번호: [안전한 비밀번호 설정]

✅ Wi-Fi 설정
   - SSID: [네트워크 이름]
   - 비밀번호: [Wi-Fi 비밀번호]
   - 국가: KR (대한민국)

✅ 로케일 설정
   - 시간대: Asia/Seoul
   - 키보드 레이아웃: us

✅ 호스트명 설정
   - 호스트명: pathfinder-kit
```

6. **이미지 작성 시작** (SD 카드의 모든 데이터가 삭제됩니다)

## 🚀 2단계: 첫 부팅 및 네트워크 연결

### Pi Zero 2 W 부팅
1. **microSD 카드를 Pi Zero 2 W에 삽입**
2. **전원 연결** (5V 2A 이상 권장)
3. **부팅 대기** (첫 부팅은 2-3분 소요)
4. **LED 상태 확인**:
   - 🔴 **빨간색 LED**: 전원 공급 정상
   - 🟢 **초록색 LED**: 시스템 활동 (깜빡임)

### IP 주소 찾기
다음 방법 중 하나를 사용하여 Pi의 IP 주소를 확인:

#### 방법 1: 라우터 관리 페이지
```
1. 라우터 관리 페이지 접속 (보통 192.168.1.1 또는 192.168.0.1)
2. 연결된 기기 목록에서 'pathfinder-kit' 찾기
```

#### 방법 2: 네트워크 스캔 도구
```bash
# Windows (Advanced IP Scanner 사용)
# macOS/Linux
nmap -sn 192.168.1.0/24
```

#### 방법 3: mDNS 사용
```bash
ping pathfinder-kit.local
```

## 🔐 3단계: SSH 연결

### SSH 클라이언트 사용
```bash
# 호스트명으로 연결 (권장)
ssh pi@pathfinder-kit.local

# 또는 IP 주소로 연결
ssh pi@192.168.1.XXX
```

### 첫 연결 시 주의사항
```
The authenticity of host 'pathfinder-kit.local' can't be established.
ECDSA key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
```
**"yes" 입력하여 계속 진행**

### 로그인
- **사용자명**: `pi`
- **비밀번호**: 설정한 비밀번호 입력

## ⚙️ 4단계: 시스템 초기 설정

### 비밀번호 변경 (보안 강화)
```bash
passwd
# 현재 비밀번호 입력 후 새 비밀번호 설정
```

### 시스템 업데이트
```bash
# 패키지 목록 업데이트
sudo apt update

# 시스템 업그레이드 (시간이 오래 걸릴 수 있음)
sudo apt upgrade -y

# 불필요한 패키지 제거
sudo apt autoremove -y
```

### 필수 패키지 설치
```bash
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-rpi.gpio \
    python3-picamera2 \
    git \
    vim \
    htop \
    tree \
    curl \
    wget
```

## 🔧 5단계: 하드웨어 인터페이스 활성화

### raspi-config 실행
```bash
sudo raspi-config
```

### 설정 항목들
```
1. Interface Options → Camera → Enable
   (카메라 모듈 활성화)

2. Interface Options → I2C → Enable
   (I2C 통신 활성화)

3. Interface Options → SPI → Enable
   (SPI 통신 활성화)

4. Advanced Options → Expand Filesystem
   (SD 카드 전체 용량 사용)

5. System Options → Boot / Auto Login → Console Autologin
   (자동 로그인 설정)

6. Localisation Options → Timezone → Asia → Seoul
   (시간대 설정)
```

### 재부팅
```bash
sudo reboot
```

## 📁 6단계: 패스파인더 키트 소스코드 설치

### 저장소 클론
```bash
cd ~
git clone https://github.com/yourusername/Pathfinder-Kit.git
cd Pathfinder-Kit
```

### Python 가상환경 생성 (권장)
```bash
# 가상환경 생성
python3 -m venv pathfinder-env

# 가상환경 활성화
source pathfinder-env/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 환경 변수 설정
```bash
# .bashrc에 환경 변수 추가
echo 'export PATHFINDER_HOME=~/Pathfinder-Kit' >> ~/.bashrc
echo 'alias pathfinder="cd $PATHFINDER_HOME"' >> ~/.bashrc
source ~/.bashrc
```

## 🧪 7단계: 시스템 테스트

### GPIO 권한 확인
```bash
groups
# 출력에 'gpio' 그룹이 포함되어야 함
```

### 카메라 테스트
```bash
# 카메라 모듈 인식 확인
libcamera-hello --timeout 2000

# 사진 촬영 테스트
libcamera-still -o test.jpg --timeout 2000
```

### GPIO 핀 상태 확인
```bash
# GPIO 핀 맵 확인
pinout

# 또는 상세 정보
gpio readall
```

### 시스템 정보 확인
```bash
# 시스템 정보
cat /proc/cpuinfo | grep Model

# 메모리 사용량
free -h

# 디스크 사용량
df -h
```

## 🌐 8단계: 네트워크 최적화 (선택사항)

### 고정 IP 설정 (권장)
```bash
sudo nano /etc/dhcpcd.conf

# 파일 끝에 추가:
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4
```

### SSH 보안 강화
```bash
sudo nano /etc/ssh/sshd_config

# 다음 설정 변경:
Port 2222                    # 기본 포트 변경
PermitRootLogin no          # root 로그인 금지
MaxAuthTries 3              # 인증 시도 제한
```

## 🔧 문제 해결

### 일반적인 문제들

#### SSH 연결이 안 되는 경우
```bash
# 1. Pi가 네트워크에 연결되었는지 확인
ping pathfinder-kit.local

# 2. SSH 서비스 상태 확인 (Pi에서 직접)
sudo systemctl status ssh

# 3. 방화벽 확인
sudo ufw status
```

#### Wi-Fi 연결 문제
```bash
# Wi-Fi 상태 확인
iwconfig

# 네트워크 재시작
sudo systemctl restart networking

# Wi-Fi 설정 재구성
sudo raspi-config
```

#### 카메라 인식 문제
```bash
# 카메라 모듈 확인
vcgencmd get_camera

# 출력: supported=1 detected=1 (정상)
```

#### 메모리 부족 문제
```bash
# 스왑 파일 크기 증가
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=1024 (1GB로 증가)
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 📋 최종 확인 체크리스트

### 네트워크 & 접속
- [ ] SSH 연결 성공
- [ ] 인터넷 연결 확인 (`ping google.com`)
- [ ] 고정 IP 설정 (선택사항)

### 하드웨어 인터페이스
- [ ] 카메라 모듈 인식
- [ ] GPIO 핀 접근 가능
- [ ] I2C/SPI 활성화

### 소프트웨어 환경
- [ ] Python 3.7+ 설치 확인
- [ ] 필수 패키지 설치 완료
- [ ] 패스파인더 키트 소스코드 다운로드

### 보안 설정
- [ ] 기본 비밀번호 변경
- [ ] SSH 보안 설정 (선택사항)
- [ ] 방화벽 설정 (선택사항)

## 🎉 설정 완료!

축하합니다! Raspberry Pi Zero 2 W 설정이 완료되었습니다.
이제 [Flask 대시보드 사용법 가이드](2_Usage_Flask_Dashboard.md)로 넘어가세요.

## 📞 추가 도움말

### 유용한 명령어들
```bash
# 시스템 재시작
sudo reboot

# 시스템 종료
sudo shutdown -h now

# 네트워크 정보 확인
ip addr show

# 시스템 로그 확인
sudo journalctl -f

# 온도 확인
vcgencmd measure_temp
```

### 성능 모니터링
```bash
# CPU 사용률 실시간 모니터링
htop

# 시스템 리소스 확인
top

# 디스크 I/O 모니터링
iotop
```

---

**💡 팁: SSH 연결이 끊어지면 `screen` 또는 `tmux`를 사용하여 세션을 유지하세요!**
